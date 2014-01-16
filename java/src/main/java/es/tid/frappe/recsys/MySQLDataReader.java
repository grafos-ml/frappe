/*
 * The MySQL data reader for the FFOS recomendation algorithms.
 * 
 */

package es.tid.frappe.recsys;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;
import org.jblas.FloatMatrix;


/**
 * This is a MySQL interface for read the matrix from the db and the matrix 
 * dimension.
 * 
 * @author João Baptista <joaonrb@gmail.com>
 * @since 18 Nov 2013
 */
public class MySQLDataReader extends SQLConnection implements DataReader {

    private int[] dims;
    
    /**
     * See implemented abstract class here
     * {@link es.tid.frappe.recsys.SQLConnection#setConnection }
     * 
     * @param host
     * @param port
     * @param dbname
     * @param user
     * @param pswd 
     */
    public MySQLDataReader(String host, int port, String dbname, String user,
            String pswd) throws SQLException {
        super(host, port, dbname, user, pswd);
    }
   


    @Override
    public FloatMatrix getData() {
        ResultSet rs;
        List<float[]> fs = new ArrayList<float[]>();
        //FloatMatrix ctxt_data = new FloatMatrix();
        try {
            rs = this.executeQuery("SELECT * FROM ffos_installation " +
                "ORDER BY user_id;");  
            while(rs.next()) {
                fs.add(new float[]{
                    rs.getInt("user_id"),
                    rs.getInt("app_id")
                });
            }
            rs.close();
        } catch(SQLException e) {
            Logger lgr = Logger.getLogger(MySQLDataReader.class.getName());
            lgr.log(Level.SEVERE, e.getMessage(), e);
        }
        float[][] array = new float[fs.size()][];
        for(int i=0;i<fs.size();i++)
            array[i] = fs.get(i);
        return new FloatMatrix(array);
    }

    /**
     * MySQL get dimensions array method.
     * 
     * This function is a bit deferent from the Mongo version. Mongo had some
     * setup structure that help the getDims. Besides it might not be well
     * constructed and it probably have some changes in the future.
     * 
     * @return
     *      An array of int with all the dimensions needed to build the matrix.
     *      it should be something like this:
     *      [num_users, num_apps, num_options_ctxt1, num_options_ctxt2, ...]
     */
    @Override
    public int[] getDims() {
        if (this.dims == null) {
            int users = 0, apps = 0;
            ResultSet rs_user = null, rs_app = null;
            try {
                rs_user = this.executeQuery("SELECT COUNT(*) "
                        + "FROM ffos_ffosuser;");
                users = rs_user.next() ? rs_user.getInt(1) : 0;
                rs_app = this.executeQuery("SELECT COUNT(*) "
                        + "FROM ffos_ffosapp;");
                apps = rs_app.next() ? rs_app.getInt(1) : 0;
            } catch(SQLException e) {
                Logger lgr = Logger.getLogger(MySQLDataReader.class.getName());
                lgr.log(Level.SEVERE, e.getMessage(), e);
            }
            // Now just return [dim_users, dim_apps]:: to be improved
            this.dims = new int[]{users,apps};
        }
        return this.dims;
    }
}
