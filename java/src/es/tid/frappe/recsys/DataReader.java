package es.tid.frappe.recsys;

import org.jblas.FloatMatrix;

public interface DataReader {
	
	/**
	 * Reads a data in the matrix format.
	 * Each row is:
	 * user,item,context1,context2,context3,count
	 * @return
	 */
	public FloatMatrix getData();
	
	/**
	 * Returns how many entries there is in each dimension. For example 100 users 10 items, 5 c1:
	 * [100, 10, 5]
	 * @return number of entries in each dimension.
	 */
	public int[] getDims();
}
