package es.tid.frappe.python;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintStream;
import java.util.List;

import org.jblas.FloatMatrix;

import es.tid.frappe.recsys.TensorCoFi;

public class TensorCoPy {
	
	/**
	 * 
	 * @param args: 
	 * 				String <datapath, dim, niter, lambda, alpha, dim0, dim1
	 * @throws IOException 
	 */
	public static void main(String[] args) throws IOException {
		PrintStream out = System.out;
		System.setOut(new PrintStream(new OutputStream() {
		    @Override public void write(int b) throws IOException {}
		}));
		FloatMatrix data = FloatMatrix.loadCSVFile(args[0]+"train.csv");
		TensorCoFi ts = new TensorCoFi(Integer.valueOf(args[1]), 
				Integer.valueOf(args[2]), Float.valueOf(args[3]),
				Float.valueOf(args[4]),new int[]{Integer.valueOf(args[5]),
			Integer.valueOf(args[6])});
		ts.train(data);
		List<FloatMatrix> model = ts.getModel();
		floatMatrixToCSV(model.get(0),args[0]+"user.csv");
		floatMatrixToCSV(model.get(1),args[0]+"item.csv");
		System.setOut(out);
		System.out.print(args[0]+"user.csv ");
		System.out.print(args[0]+"item.csv");
	}
	
	private static void floatMatrixToCSV(FloatMatrix fm, String fpath) {
		StringBuilder sb = new StringBuilder();
		for(int row = 0; row < fm.rows; row++) {
			for(int column = 0; column < fm.columns; column++)
				sb.append(String.valueOf(fm.get(row,column)))
					.append((column+1==fm.columns)?"":",");
			sb.append('\n');
		}
		
		try {
			FileWriter fw = new FileWriter(new File(fpath),true);
			fw.write(sb.toString());
			fw.close();
		} catch (IOException e) {
			e.printStackTrace();
			System.exit(1);
		}
	}
}
