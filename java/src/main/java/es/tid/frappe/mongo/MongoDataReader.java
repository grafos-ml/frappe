package es.tid.frappe.mongo;

import java.io.IOException;
import java.net.UnknownHostException;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.jblas.FloatMatrix;

import com.mongodb.BasicDBList;
import com.mongodb.BasicDBObject;
import com.mongodb.DB;
import com.mongodb.DBCollection;
import com.mongodb.DBCursor;
import com.mongodb.DBObject;
import com.mongodb.Mongo;

import es.tid.frappe.recsys.DataReader;


/**
*
* @author pev
* 
*/
public class MongoDataReader implements DataReader {
	private static final String ctxt_coll_name = "discctxt";
	private static final String setup_coll_name = "setup";
	private static final String users_coll_name = "users";
	private static final String apps_coll_name = "applications";
	private static final String counters_coll_name = "counters";
	private final String host;
	private final int port;
	private final Mongo m;
	private final DB db;
	private final DBCollection ctxt_coll;
	private final DBCollection setup_coll;
	private final DBCollection counters_coll;
	public int[] dims = null;
	
	public MongoDataReader(String host, int port, String dbname, String user, String pswd) throws UnknownHostException {
		this.host = host;
		this.port = port;
		this.m = new Mongo(host, port);
		this.db = m.getDB(dbname);
		if (user != null & pswd != null)
			this.db.authenticate(user, pswd.toCharArray());
		this.ctxt_coll = db.getCollection(ctxt_coll_name);
		this.setup_coll = db.getCollection(setup_coll_name);
		this.counters_coll = db.getCollection(counters_coll_name);
		
		System.out.println("\tMongoDataReader " + dbname + "@" + host + ":" + port + " (" + ctxt_coll.getCount() + " disc ctxt arrays)");
//		System.out.println("\tNum discretized context arrays: " + ctxt_coll.getCount());
		BasicDBObject apps_counter_ref = new BasicDBObject("_id", apps_coll_name);
//		System.out.println("\tApplications counter: " + (Integer)counters_coll.findOne(apps_counter_ref).get("value"));
		BasicDBObject users_counter_ref = new BasicDBObject("_id", users_coll_name);
//		System.out.println("\tUsers counter: " + (Integer)counters_coll.findOne(users_counter_ref).get("value"));
	}

	/**
	 * Generate ctxt data matrix:
	 * [
	 *  [user_frappe_id1, app_frappe_id1, ctxt1_val1, ctxt2_val1, ..., count],
	 *  ...
	 *  [user_frappe_id1, app_frappe_id1, ctxt1_valX, ctxt2_val1, ..., count],
	 *  ...
	 *  [user_frappe_id1, app_frappe_idM, ctxt1_val1, ctxt2_val1, ..., count],
	 *  ...
	 *  [user_frappe_idN, app_frappe_id1, ctxt1_val1, ctxt2_val1, ..., count],
	 *  ...
	 * ]
	 */
	@Override
	public FloatMatrix getData() {
		// Declarations
		BasicDBObject sort_filter = new BasicDBObject("fi", 1);
		sort_filter.put("ra", 1);
		DBCursor ctxt_cur = this.ctxt_coll.find().sort(sort_filter);
		int num_dims = this.getDims().length + 1;
		int num_ctxt = (int)this.ctxt_coll.count();
		FloatMatrix ctxt_data = new FloatMatrix(num_ctxt, num_dims);
		System.out.println("\tREADING DISC CTXT MATRIX [" + ctxt_data.rows + " x " + ctxt_data.columns + "]...");
		int loop = 0;
		while (ctxt_cur.hasNext()) {
			int i = 0;
			DBObject ctxt_doc = ctxt_cur.next();
			// Retrieve ctxt document data
			int user_id = (Integer)ctxt_doc.get("fi");
			int app_id = (Integer)ctxt_doc.get("ra");
			BasicDBList dbl = (BasicDBList)ctxt_doc.get("x");
                        Object n = ctxt_doc.get("n");
                        float score = 0;
                        if (n instanceof Integer)
                            score = (Integer)n;
                        if (n instanceof Float)
                            score = (Float)n;
			// Add data to matrix
			ctxt_data.put(loop, i, (float)user_id);
			i++;
			ctxt_data.put(loop, i, (float)app_id);
			i++;
			for (int ind=0; ind<dbl.size(); ind++) {
				int ctxt_val = (Integer)dbl.get(ind);
				ctxt_data.put(loop, i, (float)ctxt_val);
				i++;
			  }
			ctxt_data.put(loop, i, score);
			i++;
                        //System.out.println(ctxt_data.getRow(loop).toString());
			loop++;
                        
		}
                try {
                    ctxt_data.save("data.jblas");
                } catch (IOException ex) {
                    Logger.getLogger(MongoDataReader.class.getName()).log(Level.SEVERE, null, ex);
                }
		return ctxt_data;
	}

	/**
	 * Generate dimensions array: number of options for each dimension:
	 * [num_users, num_apps, num_options_ctxt1, num_options_ctxt2, ...]
	 */
	@Override
	public int[] getDims() {
		if (this.dims != null) {
			return this.dims;
		}
		BasicDBObject query = new BasicDBObject();
		query.put("_id", "ctxt_dimensions");
		DBObject setup = setup_coll.findOne(query);
		BasicDBList dbl = (BasicDBList)setup.get("dims");
		this.dims = new int[dbl.size() + 2];
//		dims[0] = (int)users_coll.getCount() + 1;
//		dims[1] = (int)apps_coll.getCount() + 1;
		BasicDBObject users_counter_ref = new BasicDBObject("_id", users_coll_name);
		BasicDBObject apps_counter_ref = new BasicDBObject("_id", apps_coll_name);
		dims[0] = (Integer)counters_coll.findOne(users_counter_ref).get("value") + 1;
		dims[1] = (Integer)counters_coll.findOne(apps_counter_ref).get("value") + 1;
		for (int i=0; i<dbl.size(); i++) {
		    dims[i + 2] = (Integer)dbl.get(i);
		  }
		String to_print = "\tDimensions to read (" + dims.length + "): [";
		for (int i=0; i < dims.length; i++) {
			to_print += dims[i] + ", ";
		}
		to_print += "]";
		System.out.println(to_print);
		return dims;
	}

}
