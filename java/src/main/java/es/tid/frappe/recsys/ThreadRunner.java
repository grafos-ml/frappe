/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package org.cofirank.tensorcofi.predictors;

import java.util.ArrayList;
import java.util.HashMap;
import org.jblas.FloatMatrix;

/**
 *
 * @author mumas
 */
public class ThreadRunner implements Runnable{

    int dimension, start, end;
    TFThreads tensor;
    FloatMatrix dataArray, base, factorMatrix;
    ArrayList<HashMap<Integer, ArrayList<Integer>>> tensorIndex;
    float pikj;

    public ThreadRunner(int start, int end, FloatMatrix factorMatrix, int dimension, TFThreads tensor, FloatMatrix dataArray, FloatMatrix base,
            ArrayList<HashMap<Integer, ArrayList<Integer>>> tensorIndex) {
        this.dimension = dimension;
        this.tensor = tensor;
        this.dataArray = dataArray;
        this.base = base;
        this.tensorIndex = tensorIndex;
        this.factorMatrix = factorMatrix;
        this.start = start;
        this.end = end;
    }


    public void updateSingleEntry(int dataEntry){
         float pijk = tensor.getCounts().get(dimension).get(dataEntry,0);
            ArrayList<Integer> dataRowList = this.tensorIndex.get(dimension).get(dataEntry);
            FloatMatrix newEntry = TFThreads.computeNewTensorEntrieVector(
                    dataRowList, tensor.getFactors(), tensor.getP(), pijk,
                    tensor.dimensionEntries[dimension], tensor.getD(), tensor.getLambda(), dimension,
                    base, this.dataArray);

            synchronized(this.factorMatrix){
                this.factorMatrix.putColumn(dataEntry, newEntry);
            }
    }

    public void run(){
        for (int dataEntry = this.start; dataEntry < this.end; dataEntry++){
            updateSingleEntry(dataEntry);
        }
    }

}
