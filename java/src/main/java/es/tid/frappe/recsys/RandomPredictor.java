package es.tid.frappe.recsys;

import java.util.List;
import java.util.Random;

import org.jblas.FloatMatrix;
/**
 *
 * @author mumas
 */
public class RandomPredictor implements Predictor{

    Random r = new Random();

    @Override
    public float decision(FloatMatrix tupple) {
        return r.nextInt(5)+1;
    }   

    @Override
    public String getName() {
        return "Random Predictor.";
    }
    
    @Override
    public void train(FloatMatrix data) {
    }

	@Override
	public List<FloatMatrix> getModel() {
		// TODO Auto-generated method stub
		// FIXME linas will implement
		return null;
	}

}
