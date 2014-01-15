/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

package es.tid.frappe.recsys;

import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.sql.SQLException;
import java.util.Arrays;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;
import org.apache.commons.codec.binary.Base64;
import org.apache.commons.lang3.ArrayUtils;
import org.jblas.FloatMatrix;

/**
 *
 * @author joaonrb
 */
public class MySQLDataWriter extends SQLConnection implements DataWriter {

    public MySQLDataWriter(String host, int port, String dbname, String user,
            String pswd) throws SQLException {
        super(host, port, dbname, user, pswd);
    }

    // Linas code
    
    /**
     * Converts 64bit encoded string to the float[][] array.
     * Linas method<linas@tid.es>
     * 
     * @param encodedMatrixStr
     * @param rows
     * @param columns
     * @return float[][]
     */
    private float[][] base64toFloatArray(String encodedMatrixStr, int rows, 
            int columns) {
        // First we take the string as a byte array
        byte[] bb = ByteBuffer.wrap(Base64.decodeBase64(encodedMatrixStr))
                .array();    
        // I am not sure why, but bytes are in reverse order..., so we fix that
        ArrayUtils.reverse(bb);
        // Now we construct float array from these bytes. Each number is 
        // 64 bits = 8 bytes
        float[] floats = new float[bb.length / 8];
        for (int i = 0; i < floats.length; i++){
            byte[] copyOfRange = Arrays.copyOfRange(bb, i*8, i*8+8);
            floats[i] = (float)toDouble(copyOfRange);
        }
        // We also get it in the wrong order :) so we reverse back
	ArrayUtils.reverse(floats);
		
	//now from 1d array we convert to 2d array
	float array2d[][] = new float[rows][columns];
	for(int j=0;j<rows;j++)
		for(int i=0; i<columns;i++)
			array2d[j][i] = floats[(j*columns) + i];
	return array2d;
    }
    
    /**
     * This is also Linas made
     * @param bytes
     * @return 
     */
    private static double toDouble(byte[] bytes) {
	    return ByteBuffer.wrap(bytes).getDouble();
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
