package es.tid.frappe.recsys;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.jblas.FloatMatrix;
/**
 *  Counts how many times the item was used.
 * 
 * @author mumas
 */
public class PopPredictor implements Predictor{
    private Map<Integer, Float> popPreds = new HashMap<Integer, Float>();
    private FloatMatrix dataArray;


    public void train(FloatMatrix trainData){
        dataArray = trainData;
    }
    
    @Override
    public float decision(FloatMatrix tupple) {
        float sum = 0;
        int i = (int)tupple.get(1);
        if (popPreds.containsKey(i)){
            return popPreds.get(i);
        }

        FloatMatrix items = dataArray.getColumn(1);
        FloatMatrix counts = dataArray.getColumn(dataArray.columns-1);

        for (int j = 0; j < items.length; j++) {
            if (items.get(j) == i){
                sum += counts.get(j);
            }
        }
        float p = (float)sum;
        popPreds.put(i, p);
        return p;
    }

    @Override
    public String getName() {
        return "Popularity.";
    }

	@Override
	public List<FloatMatrix> getModel() {
		// TODO Auto-generated method stub
		// Linas will implement
		return null;
	}

}
