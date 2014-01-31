/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

package es.tid.frappe.mysql;

import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.sql.SQLException;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.apache.commons.codec.binary.Base64;
import org.jblas.FloatMatrix;

import es.tid.frappe.recsys.DataWriter;
import es.tid.frappe.recsys.SQLConnection;

/**
 *
 * @author joaonrb
 */
public class MySQLDataWriter extends SQLConnection implements DataWriter {

    public MySQLDataWriter(String host, int port, String dbname, String user,
            String pswd) throws SQLException {
        super(host, port, dbname, user, pswd);
    }

    private String floatArrayToBase64String(float[] array) throws IOException {
		byte[] encodeBase64 = Base64.encodeBase64(toByteArray(array));
		return new String(encodeBase64, "UTF-8");
	}
        
    private byte[] toByteArray(float[] fArr) throws IOException{
	double[] array = convertFloatsToDoubles(fArr);
	ByteArrayOutputStream bas = new ByteArrayOutputStream();
	DataOutputStream ds = new DataOutputStream(bas);
	for (double f : array) 
	    ds.writeDouble(f);
	byte[] bytes = bas.toByteArray();
	return bytes;
    }
        
    private static double[] convertFloatsToDoubles(float[] input) {
	if (input == null) 
            return null; // Or throw an exception - your choice
	double[] output = new double[input.length];
	for (int i = 0; i < input.length; i++) 
            output[i] = input[i];
	return output;
    }
        // End of Linas code
    
     private void insertMatrix(FloatMatrix u, int dim) throws IOException,
             SQLException {
         String query = new StringBuilder(
            "INSERT INTO  recommender_factor (`id`, `dimension`, `matrix`, ")
            .append("`rows`, `columns`) VALUES (NULL, '")
            .append(dim).append("', '")
            .append(floatArrayToBase64String(u.toArray())).append("', '")
            .append(u.rows).append("', '").append(u.columns).append("');")
            .toString();
         System.out.print(query);
         this.executeUpdate(query);
    }

        
    @Override
    public void writeModel(List<FloatMatrix> model) {
        int i = 0;
        for(FloatMatrix fm : model) {
            try {
                this.insertMatrix(fm, i);
            } catch(Exception e) {
                Logger lgr = Logger.getLogger(MySQLDataReader.class.getName());
                lgr.log(Level.SEVERE, e.getMessage(), e);
            } finally {
                i++;
            }
        }
        
    }
    
}
