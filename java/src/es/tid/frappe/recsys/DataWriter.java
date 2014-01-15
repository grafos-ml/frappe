package es.tid.frappe.recsys;

import java.util.List;

import org.jblas.FloatMatrix;

public interface DataWriter {
	public void writeModel(List<FloatMatrix> model);
}
