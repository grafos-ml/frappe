package es.tid.frappe.python;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintStream;
import java.util.List;

import org.jblas.FloatMatrix;

import es.tid.frappe.recsys.TensorCoFi;
import es.tid.frappe.recsys.TFThreads;

public class TensorCoPy {
	
	/**
	 * 
	 * @param args: 
	 * 				String <datapath, dim, niter, lambda, alpha, dim0, dim1
	 * @throws IOException 
	 */
	public static void main(String[] args) throws IOException {
        String directory = System.getProperty("directory");
        int number_of_factors = Integer.valueOf(System.getProperty("n_factors"));
        int number_of_iterations = Integer.valueOf(System.getProperty("n_iterations"));
        float lambda = Float.valueOf(System.getProperty("lambda"));
        float alpha = Float.valueOf(System.getProperty("alpha"));
        int number_of_contexts = Integer.valueOf(System.getProperty("n_contexts"));
        String contexts[] = new String[number_of_contexts];
        int dimensions[] = new int[number_of_contexts];
        for(int i=0; i<number_of_contexts; i++) {
            contexts[i] = System.getProperty("context" + i);
            dimensions[i] = Integer.valueOf(System.getProperty("dimension" + i));
        }
        String path;

        // Stop the output
		PrintStream out = System.out;
		System.setOut(new PrintStream(new OutputStream() {
		   @Override public void write(int b) throws IOException {}
		 }));
<<<<<<< HEAD
		FloatMatrix data = FloatMatrix.loadCSVFile(directory+"train.csv");
		TensorCoFi ts = new TensorCoFi(number_of_factors, number_of_iterations, lambda, alpha, dimensions);
=======
		FloatMatrix data = FloatMatrix.loadCSVFile(args[0]+"train.csv");
		TensorCoFi ts = new TensorCoFi(Integer.valueOf(args[1]), 
				Integer.valueOf(args[2]), Float.valueOf(args[3]),
				Float.valueOf(args[4]),new int[]{Integer.valueOf(args[5]),
			Integer.valueOf(args[6])});
>>>>>>> real-time
		ts.train(data);
		List<FloatMatrix> model = ts.getModel();
        // Start the output
        System.setOut(out);
        for(int i=0; i<number_of_contexts; i++) {
            path = directory + contexts[i] +".csv";
            floatMatrixToCSV(model.get(i), path);
            System.out.print(path + (i == number_of_contexts-1 ? "" : " "));
        }
	}
	
	private static void floatMatrixToCSV(FloatMatrix fm, String fpath) {
		StringBuilder sb = new StringBuilder();
		for(int row = 0; row < fm.rows; row++) {
			for(int column = 0; column < fm.columns; column++)
				sb.append(String.valueOf(fm.get(row,column)))
					.append((column+1==fm.columns) ? "" : ",");
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
