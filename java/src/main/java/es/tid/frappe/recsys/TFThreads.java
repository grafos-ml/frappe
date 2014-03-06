package org.cofirank.tensorcofi.predictors;

import org.jblas.FloatMatrix;
import org.jblas.Solve;
import java.util.ArrayList;
import java.util.List;
import java.util.HashMap;
import java.util.Iterator;
import org.cofirank.tensorcofi.TensorOptions;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 *
 * @author mumas
 */
public class TFThreads implements Predictor {

    protected int[] dimensionEntries;
    private int numDim;
    private int d;
    private float p;
    private float lambda;
    private ArrayList<FloatMatrix> Factors;
    private ArrayList<FloatMatrix> Counts;
    private static final int NUMBER_OF_THREADS = 5;

    public TFThreads(TensorOptions options, int[] dimensions) {
        this.dimensionEntries = dimensions;
        this.d = options.d;
        this.lambda = (float) options.lambda;

        this.Factors = new ArrayList<FloatMatrix>();
        this.Counts = new ArrayList<FloatMatrix>();
        this.p = options.p;

        for (int i = 0; i < this.numDim; i++) {
            FloatMatrix tempFactors = FloatMatrix.rand(this.d, this.dimensionEntries[i]);
            this.Factors.add(tempFactors);
        }

        for (int i = 0; i < this.numDim; i++) {
            FloatMatrix tempFactors = FloatMatrix.zeros(this.dimensionEntries[i],1);
            this.Counts.add(tempFactors);
        }

    }

    public void update(int[] Data) {
    }

   public void solve(int numIter, FloatMatrix dataArray) {

        FloatMatrix base = FloatMatrix.ones(this.getD(), this.getD());
        ArrayList<HashMap<Integer, ArrayList<Integer>>> tensor = new ArrayList<HashMap<Integer, ArrayList<Integer>>>();
   
        int counts;
        

        //System.out.print("\n"+" Starting Tensor index Datastructure build"+"\n");

        long startTime = System.nanoTime();
        //Build Tensor indices with HashMaps
        for (int i = 0; i < this.getNumDim(); i++) {
            tensor.add(new HashMap<Integer, ArrayList<Integer>>());
            for (int j = 0; j < this.dimensionEntries[i]; j++)
                tensor.get(i).put(j, new ArrayList<Integer>());
            for (int dataRow = 0; dataRow < dataArray.rows; ++dataRow)
                tensor.get(i).get((int) dataArray.get(dataRow, i) - 1).add(dataRow);
        }
        long endTime = System.nanoTime();
        long duration = endTime - startTime;
        System.out.print("\n"+" Tensor index Datastructure build in :" + duration);

        startTime = System.nanoTime();

        //Outer loop defines the number of epochs
        for (int iter = 0; iter < numIter; iter++) {
            //Iterate over each Factor Matrix (U,M,C_i...)
            for (int dimension = 0; dimension < this.getNumDim(); dimension++) {
                int entriesInDimension = dimensionEntries[dimension];
                base = FloatMatrix.ones(this.getD(), this.getD());
                //Do the base computation
                if (this.getNumDim() == 2) {
                    base = this.getFactors().get((dimension == 0) ? 1 : 0);
                    base = base.mmul(base.transpose());
                } else {
                    for (int matrixIndex = 0; matrixIndex < this.getNumDim(); matrixIndex++) {
                        if (matrixIndex != dimension) {
                            base = base.mul(this.getFactors().get(matrixIndex).mmul(this.getFactors().get(matrixIndex).transpose()));
                        }
                    }
                }

                if(iter ==0){
                // Count number of items per context value
                for (int dataEntry = 0; dataEntry < entriesInDimension; dataEntry++) {
                    counts = 0;
                    //Look up fo the entries of dataEntry in the matrixEntry column in dataArray
                    for (int dataRow = 0; dataRow < dataArray.rows; ++dataRow) {
                        if ((dataArray.get(dataRow, dimension) - 1) == dataEntry) {
                            counts++;
                        }
                        if(counts ==0 )
                            counts = 1;
                        this.getCounts().get(dimension).put(dataEntry,0,(float) counts);
                    }
                  }
                }

                // Iterate over each row in dimension
                // we will paralelize this part
                ExecutorService executor = Executors.newFixedThreadPool(NUMBER_OF_THREADS);
                int stepPerThread = entriesInDimension / NUMBER_OF_THREADS;
                if (stepPerThread == 0) // if there are more threads than entriesindimension
                    stepPerThread = 1;
                for (int start = 0; start < entriesInDimension; start += stepPerThread){
                    int end = (start+stepPerThread < entriesInDimension)? start+stepPerThread : entriesInDimension;
                    //System.out.println("adding thread - start:"+start+" end:"+end+" total entries in dim:"+entriesInDimension);
                    Runnable worker = new ThreadRunner(start, end, this.getFactors().get(dimension), dimension, this, dataArray, base, tensor);
                    executor.submit(worker);
                }

                                
                                        
//                    float pijk = this.getCounts().get(dimension).get(dataEntry,0);
//                    ArrayList<Integer> dataRowList = tensor.get(dimension).get(dataEntry);
//                    FloatMatrix entry = computeNewTensorEntrieVector(dataRowList, this.getFactors(), this.getP(), pijk, entriesInDimension, this.getD(), this.getLambda(), dimension, base, dataArray);
//                    this.getFactors().get(dimension).putColumn(dataEntry, entry);
//
                
		executor.shutdown();
                
            }

        }
            endTime = System.nanoTime();
            duration = endTime - startTime;
            System.out.print("\n"+ "Optimization took: " + duration/1000000000);
    }

    public static FloatMatrix computeNewTensorEntrieVector(ArrayList<Integer> dataRowList,
            final ArrayList<FloatMatrix> factors, float p, float pijk, int entriesInDimension, int d, float lambda, 
            int dimension, final FloatMatrix base, final FloatMatrix dataArray){
        
        FloatMatrix temp = FloatMatrix.ones(d, 1); //temporary vector for the factor-factor... element-wise product storage
        FloatMatrix regularizer = FloatMatrix.eye(d).mul(lambda);
        FloatMatrix matrixVectorProd = FloatMatrix.zeros(d, 1);
        FloatMatrix invertible = FloatMatrix.zeros(d, d);
        FloatMatrix one = FloatMatrix.eye(d);
        float weight;
        
        Iterator<Integer> iterator = dataRowList.iterator();
        while(iterator.hasNext()){
            int dataRow = iterator.next();
            temp = temp.mul((float) 0.0).addi((float) 1.0);
            for (int dataCol = 0; dataCol < dataArray.columns - 1; dataCol++) {
                if (dataCol != dimension) {   // we should check if row-wise is faster
                    //Do the multiplication of all the relevant factors in each dimension
                    temp = temp.muliColumnVector(factors.get(dataCol).getColumn((int) dataArray.get(dataRow, dataCol) - 1));
                }
            }//update the invertible
            weight =  (float) (1.0 + p * Math.log(1.3+ (float) entriesInDimension / (pijk + 1.0)) + (float)(dataArray.get(dataRow, dataArray.columns - 1)));
            invertible = invertible.rankOneUpdate((float) (weight - 1.0), temp);
            //targetValue = (float) Math.log(1.0 + dataArray.get(dataRow, dataArray.columns - 1)/0.5);
            // update the matrix vector product
            matrixVectorProd = matrixVectorProd.addColumnVector(temp.mul((float) weight));
        }
    
        invertible = invertible.addi(base);
        regularizer = regularizer.mul((float) 1.0/(float)entriesInDimension);
        invertible = invertible.addi(regularizer);
        invertible = Solve.solveSymmetric(invertible, one);
        return invertible.mmul(matrixVectorProd);
    }

    public float decision(long[] position) {

        FloatMatrix temp = FloatMatrix.ones(this.getD(), 1);
        for (int i = 0; i < position.length; i++) {
            temp = temp.mulColumnVector(this.getFactors().get(i).getColumn((int) position[i] - 1));
        }

        return temp.sum();
    }
    @Override
    public float decision(FloatMatrix position) {

        FloatMatrix temp = FloatMatrix.ones(this.getD(), 1);
        for (int i = 0; i < position.columns ; i++) {
            
            temp = temp.mulColumnVector(this.getFactors().get(i).getColumn((int) position.get(0,i) - 1));
        }

        return temp.sum();
    }

    @Override
    public String getName() {
        return "TensorCofi with Threads.";
    }

    
    /**
     * @return the numDim
     */
    public int getNumDim() {
        return numDim;
    }

    /**
     * @return the d
     */
    public int getD() {
        return d;
    }

    /**
     * @return the p
     */
    public float getP() {
        return p;
    }

    /**
     * @return the lambda
     */
    public float getLambda() {
        return lambda;
    }

    /**
     * @return the Factors
     */
    public ArrayList<FloatMatrix> getFactors() {
        return Factors;
    }

    /**
     * @return the Counts
     */
    public ArrayList<FloatMatrix> getCounts() {
        return Counts;
    }
}
