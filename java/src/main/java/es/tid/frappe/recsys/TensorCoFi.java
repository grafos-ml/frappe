package es.tid.frappe.recsys;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.jblas.FloatMatrix;
import org.jblas.Solve;

/**
 *
 * @author alexis
 */
public class TensorCoFi implements Predictor {

    private int[] dimensions; //count entries in each dimension
    
    private final int d;
    private final int iter;
    private final float p;
    private final float lambda;
    private ArrayList<FloatMatrix> Factors; //factors for each dimension
    private ArrayList<FloatMatrix> Counts;

    public TensorCoFi(int d, int iter, float lambda, float p, int[] dimensions) {
        this.d = d;
        this.dimensions = dimensions;
        this.lambda = lambda;
        this.iter = iter;

        this.Factors = new ArrayList<FloatMatrix>();
        this.Counts = new ArrayList<FloatMatrix>();
        this.p = p;

        for (int i = 0; i < this.dimensions.length; i++) {
            FloatMatrix tempFactors = FloatMatrix.rand(this.d, this.dimensions[i]);
            this.Factors.add(tempFactors);
        }

        for (int i = 0; i < this.dimensions.length; i++) {
            FloatMatrix tempFactors = FloatMatrix.zeros(this.dimensions[i],1);
            this.Counts.add(tempFactors);
        }

    }

//    }

   @Override
   public void train(FloatMatrix dataArray) {
       train(dataArray, true);
   }
   
   public void train(FloatMatrix dataArray, boolean printError) {

        FloatMatrix temp = FloatMatrix.ones(this.d, 1);
        FloatMatrix regularizer = FloatMatrix.eye(this.d).mul(this.lambda);
        FloatMatrix matrixVectorProd = FloatMatrix.zeros(this.d, 1);
        FloatMatrix one = FloatMatrix.eye(this.d);
        FloatMatrix invertible = FloatMatrix.zeros(this.d, this.d);
        FloatMatrix base = FloatMatrix.ones(this.d, this.d);
        List<Map<Integer, List<Integer>>> tensor = new ArrayList<Map<Integer, List<Integer>>>();
//        ArrayList<Integer> tmp = new ArrayList<Integer>();
        
        List<Integer> dataRowList;
        int counts, index;
        float weight;
        Map<Integer, List<Integer>> t;
        
	//System.out.println("\tBUILDING TENSOR INDICES...");
        //System.out.print("\n"+" Starting Tensor index Datastructure build"+"\n");
        //Build Tensor indices with HashMaps looping over the dimensions
        for (int i = 0; i < this.dimensions.length; i++) {
            //add into tensor one hashmap for each dimension
            tensor.add(new HashMap<Integer, List<Integer>>());
            
            //for each entry in dimension add an arraylist
            for (int j = 0; j < this.dimensions[i]; j++){
                // original
                // tensor.get(i).put(j, new ArrayList<Integer>());
                
                //João Nuno version(Correction for MySQL) The indexes there 
                //start at 1
                tensor.get(i).put(j+1, new ArrayList<Integer>());
                }
            	
            
            
            for (int dataRow = 0; dataRow < dataArray.rows; dataRow++){
                //System.out.println(dataArray.columns + " " + dataArray.rows + " " + i + " " + dataRow);
                //System.out.println(dataArray.get(dataRow, i) + " " + tensor.get(i).get((int) dataArray.get(dataRow, i)));
                index = (int) dataArray.get(dataRow, i);
                t = tensor.get(i);
                try {
                	t.get(index).add(dataRow);
                }
                catch(NullPointerException e) {
                	System.err.println("ERROR: NullPointerException accessing " + index + " of " + t.keySet().toString());
                	System.err.println("ERROR: Most probably a user or app ID does not exist");
                	throw e;
                }
            }
        }

	//System.out.println("\tTRAINING TENSOR...");
        //Outer loop defines the number of epochs
        for (int iter = 0; iter < this.iter; iter++) {
            //if (printError)
            //    System.out.println("Iteration: " + iter + " RMSE:" +
            //            getError(dataArray));
            //Iterate over each Factor Matrix (U,M,C_i...)
            for (int currentDimension = 0; currentDimension < 
                    this.dimensions.length; currentDimension++) {
                base = FloatMatrix.ones(this.d, this.d);
                //Do the base computation
                if (this.dimensions.length == 2) {
                    base = this.Factors.get((currentDimension == 0) ? 1 : 0);
                    base = base.mmul(base.transpose());
                } else {
                    for (int matrixIndex = 0; matrixIndex < this.dimensions.length; matrixIndex++) {
                        if (matrixIndex != currentDimension) {
                            base = base.mul(this.Factors.get(matrixIndex).mmul(this.Factors.get(matrixIndex).transpose()));
                        }
                    }
                }

                if(iter ==0){
                // Count number of items per context value
                for (int dataEntry = 0; dataEntry < dimensions[currentDimension]; dataEntry++) {
                    counts = 0;
                    //Look up fo the entries of dataEntry in the matrixEntry column in dataArray
                    for (int dataRow = 0; dataRow < dataArray.rows; ++dataRow) {
                        if ((dataArray.get(dataRow, currentDimension)) == dataEntry) {
                         counts++;
                        }
                        if(counts ==0 )
                            counts = 1;
                        this.Counts.get(currentDimension).put(dataEntry,0,(float) counts);
                    }
                  }
                }

                // Iterate over each row in matrixEntry
                // Original
                //for (int dataEntry = 0; dataEntry < dimensions[currentDimension];
                //        dataEntry++) {
                
                // João Nuno version
                for (int dataEntry = 1; dataEntry <= dimensions[currentDimension];
                        dataEntry++) {
                    dataRowList = tensor.get(currentDimension).get(dataEntry);
                    for(int dataRow : dataRowList){
                        //initialize the temporary vector for the factor-factor... element-wise product storage
                        temp = temp.mul((float) 0.0).addi((float) 1.0);
                        for (int dataCol = 0; dataCol < dimensions.length; dataCol++) {
                            if (dataCol != currentDimension) {   // we should check if row-wise is faster
                                //Do the multiplication
                                temp = temp.muliColumnVector(this.Factors.get(
                                    dataCol).getColumn((int) dataArray.get(
                                    dataRow, dataCol)-1));
                            }
                        }//update the invertible
                        //weight =  (float) (1.0 + this.p * FastMath.log(1.3+ (float) dimensions[currentDimension]/(this.Counts.get(currentDimension).get(dataEntry,0) + 1.0)) + (float)(dataArray.get(dataRow, dataArray.columns - 1)));
			float score = dataArray.get(dataRow, dataArray.columns - 1);
                        weight =  1.0f + this.p * (float)Math.log(1.0f + (float)(Math.abs(score)));
                        invertible = invertible.rankOneUpdate((float) (weight - 1.0), temp);
			matrixVectorProd = matrixVectorProd.addColumnVector(temp.mul((float) Math.signum(score)*weight));
                    }
                      //  }
                    //}

                    //System.out.print("DataEntry: " + dataEntry + " Counts: " + this.Counts.get(matrixEntry).get(dataEntry,0)+ "\n"+ "\n");
                    //System.out.print("Matrix Entry :"  +matrixEntry + "\n" + "Invertible Sum: "+ invertible.sum() +"\n" + "\n");
                    //System.out.print("Base: " + base.sum() +"\n"+"\n");


                    invertible = invertible.addi(base);
                    regularizer = regularizer.mul((float) 1.0/
                            (float) dimensions[currentDimension]);
                    invertible = invertible.addi(regularizer);
                    try {
                        invertible = Solve.solveSymmetric(invertible, one);
                    } catch (Exception e) {
                        System.out.print(invertible.toString());
                        e.printStackTrace();
                    }
                    
                    //Put the calulated factor back into place
                    //System.out.print("\n" + "result: " + invertible.mmul(matrixVectorProd).toString() +"\n");
                    //System.out.print("\n"+dataEntry);
                    // Original
                    //this.Factors.get(currentDimension).putColumn(dataEntry, 
                    //        invertible.mmul(matrixVectorProd));
                    
                    //João Nuno version
                    this.Factors.get(currentDimension).putColumn(dataEntry-1, 
                            invertible.mmul(matrixVectorProd));

                    // Reset invertible and matrixVectorProd
                    invertible = invertible.mul((float) 0.0);
                    matrixVectorProd = matrixVectorProd.mul((float) 0.0);
                }
            }

        }
    }

    public float decision(long[] position) {
        FloatMatrix temp = FloatMatrix.ones(this.d, 1);
        for (int i = 0; i < position.length; i++) {
            temp = temp.mulColumnVector(this.Factors.get(i).getColumn((int) position[i]));
        }
        return temp.sum();
    }
    
    @Override
    public float decision(FloatMatrix position) {

        FloatMatrix ret = FloatMatrix.ones(this.d, 1);
        for (int i = 0; i < position.columns ; i++) {
            //if (position.get(0,i) >= dimensions[i]){
            //    System.out.println(position.toString());
            //    System.out.println(Arrays.toString(dimensions));
            //}

            assert((int) position.get(0,i) < dimensions[i]);
            
            // Original
            //ret = ret.mulColumnVector(this.Factors.get(i).getColumn((int)
            //    position.get(0,i)));
            
            //João Nuno version
            ret = ret.mulColumnVector(this.Factors.get(i).getColumn((int)
                position.get(0,i)-1));
        }
        return ret.sum();
    }
     

    @Override
    public String getName() {
        return "TensorCofi.";
    }
    
	@Override
	public List<FloatMatrix> getModel() {
		return Factors;
	}

    private double getError(FloatMatrix dataArray) {
        double sum = 0.0;
        for (int dataRow = 0; dataRow < dataArray.rows; ++dataRow) {
            FloatMatrix tupple = dataArray.getRow(dataRow);
            
            float score = Math.signum(tupple.get(tupple.length-1));
            
            
            FloatMatrix copy = FloatMatrix.zeros(1, tupple.columns-1);
            for (int i=0; i<copy.columns; i++){
                copy.put(i, tupple.get(i));
            }
            float pred = this.decision(copy);
            double err = Math.pow(score-pred, 2);
            sum += err;
        }
        //System.out.println("Negs"+negs);
        return sum/dataArray.rows;
    }

}
