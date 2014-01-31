package es.tid.frappe.recsys;

import java.util.List;

import org.jblas.FloatMatrix;


/**
 *
 * @author mumas
 */
public interface Predictor {
	
    /**
     * returns a rating or ranking prediction for a user,item,context1,context2,
     * context3. In case there is no context, the format is row vector: (userId,
     * itemId)
     * @param tupple - row vector of ids: user, item, contex1, ..., contextn
     * @return evaluation score
     */
    public float decision(FloatMatrix tupple);
    
    /**
     * Returns a unique name of the method. Used in evaluation.
     * @return  
     */
    public String getName();

    /**
     * Method that trains the model, given the data.
     * @param data - A matrix, where each row is of format user,item,context1,
     * 	context2,context3, count.
     * @param dims - an integer array with the number of entries in each 
     * 	dimension. dims.lengh == data.columns-1 as there is no count.
     * 
     */
    public void train(FloatMatrix data);
    
    public List<FloatMatrix> getModel();
    
}
