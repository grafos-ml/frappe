package es.tid.frappe.mongo;

import java.net.UnknownHostException;
import java.util.List;

import org.jblas.FloatMatrix;

import com.mongodb.BasicDBList;
import com.mongodb.BasicDBObject;
import com.mongodb.DB;
import com.mongodb.DBCollection;
import com.mongodb.Mongo;

import es.tid.frappe.recsys.DataWriter;

public class MongoDataWriter implements DataWriter {
	private static final String model_coll_name = "model";
	private final String host;
	private final int port;
	private final Mongo m;
	private final DB db;
	private final String model_name;
	private final DBCollection model_coll;

	public MongoDataWriter(String host, int port, String dbname, String user, String pswd, String model_name) throws UnknownHostException {
		this.host = host;
		this.port = port;
		this.model_name = model_name;
		this.m = new Mongo(host, port);
		this.db = m.getDB(dbname);
		if (user != null & pswd != null)
			this.db.authenticate(user, pswd.toCharArray());
		// Use a collection according to model name
		this.model_coll = db.getCollection(model_coll_name + model_name);
		String msg = "\tMongoDataWriter " + dbname + "@" + host + ":" + port;
		if (model_name != "")
			msg += " - Model: " + model_name;
		System.out.println(msg);
		BasicDBObject index_keys = new BasicDBObject("f", 1);
		index_keys.put("c", 1);
		model_coll.ensureIndex(index_keys, "model_f_c", true);
	}

	public MongoDataWriter(String host, int port, String dbname, String user, String pswd) throws UnknownHostException {
		this(host, port, dbname, user, pswd, "");
	}

	@Override
	public void writeModel(List<FloatMatrix> model) {
		int count = 0;
		for (int factor = 0; factor < model.size(); factor++) {
			FloatMatrix matrix = model.get(factor);
			
			for (int ncol = 0; ncol < matrix.columns; ncol++) {
				FloatMatrix col = matrix.getColumn(ncol);
				BasicDBObject db_col_ids = new BasicDBObject("f", factor);
				BasicDBObject db_col = new BasicDBObject("f", factor);
				db_col_ids.put("c", ncol);
				db_col.put("c", ncol);
				BasicDBList lst = new BasicDBList();
				for (int i = 0; i < col.length; i++)
					lst.add(col.get(i));
				db_col.put("v", lst);
				this.model_coll.update(db_col_ids, db_col, true, false);
				count++;
			}
		}
		String msg = "\tWRITTEN " + count + " ARRAYS OF FACTORS VALUES";
		if (this.model_name != "")
			msg += " FOR MODEL " + this.model_name;
		System.out.println(msg);
	}

}
