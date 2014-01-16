package es.tid.frappe.recsys;

import com.martiansoftware.jsap.FlaggedOption;
import com.martiansoftware.jsap.JSAP;
import com.martiansoftware.jsap.JSAPException;
import com.martiansoftware.jsap.JSAPResult;
import com.martiansoftware.jsap.Parameter;
import com.martiansoftware.jsap.SimpleJSAP;
import java.lang.management.ManagementFactory;
import java.net.UnknownHostException;
import java.sql.SQLException;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.jblas.FloatMatrix;

public class ModelBuilder {

    DataReader reader;
    Map<String, DataWriter> writers = new HashMap<String, DataWriter>();
    Map<String, Predictor> predictors= new HashMap<String, Predictor>();

    public DataReader getReader() {
        return reader;
    }

    public void setReader(DataReader reader) {
        this.reader = reader;
    }

    public DataWriter getWriter(String model) {
	return this.writers.get(model);
    }

    public DataWriter getWriter() {
	return this.getWriter("default");
    }

    public void setWriter(DataWriter writer, String model) {
	this.writers.put(model, writer);
    }

    public void setWriter(DataWriter writer) {
        this.setWriter(writer, "default");
    }

    public Predictor getPred(String model) {
        return this.predictors.get(model);
    }

    public Predictor getPred() {
        return this.getPred("default");
    }

    public void setPred(Predictor pred, String model) {
        this.predictors.put(model, pred);
    }

    public void setPred(Predictor pred) {
        this.setPred(pred, "default");
    }

    public static SimpleJSAP getProgrammOptions() throws JSAPException {
        FlaggedOption optIter = new FlaggedOption("nIter")
            .setStringParser(JSAP.INTEGER_PARSER).setDefault("5")
            .setRequired(false).setShortFlag('i').setLongFlag("nIter");
        optIter.setHelp("Number of iterations the iterative algorithm will perform.");

        FlaggedOption optDim = new FlaggedOption("dim")
            .setStringParser(JSAP.INTEGER_PARSER).setDefault("20")
            .setRequired(false).setShortFlag('d').setLongFlag("dim");
        optDim.setHelp("Number of dimensions the laten features will have. Good number is in between 5 and 200 (20 - 25)");

        FlaggedOption optLambda = new FlaggedOption("lambda")
            .setStringParser(JSAP.FLOAT_PARSER).setDefault("0.05")
            .setRequired(false).setShortFlag('l').setLongFlag("lambda");
        optLambda.setHelp("The lambda regulariziation parameter. Good numer is [0.001, 0.2].");
		
        FlaggedOption optAlpha = new FlaggedOption("alpha")
            .setStringParser(JSAP.FLOAT_PARSER).setDefault("40")
            .setRequired(false).setShortFlag('a').setLongFlag("alpha");
        optAlpha.setHelp("The alpha controls the importance of observation vs "
            + "non observed values. Good numer is [5, 100].");

        FlaggedOption optMongoHost = new FlaggedOption("host")
            .setStringParser(JSAP.STRING_PARSER).setDefault("localhost")
            .setRequired(false).setShortFlag('h').setLongFlag("host");
        optMongoHost.setHelp("MongoDB server hostname.");
        FlaggedOption optMongoPort = new FlaggedOption("port")
            //.setStringParser(JSAP.INTEGER_PARSER).setDefault("27017")
            .setStringParser(JSAP.INTEGER_PARSER).setDefault("3306")
            .setRequired(false).setShortFlag('o').setLongFlag("port");
        optMongoPort.setHelp("MongoDB server listening port.");
        FlaggedOption optMongoDBname = new FlaggedOption("dbname")
            .setStringParser(JSAP.STRING_PARSER).setDefault("raqksixq_ffosv1")
            .setRequired(false).setShortFlag('n').setLongFlag("dbname");
        optMongoDBname.setHelp("MongoDB database name.");
        FlaggedOption optMongoUser = new FlaggedOption("user")
            .setStringParser(JSAP.STRING_PARSER)
            .setRequired(false).setShortFlag('u').setLongFlag("user");
        optMongoUser.setHelp("MongoDB database auth user.");
        FlaggedOption optMongoPswd= new FlaggedOption("pswd")
            .setStringParser(JSAP.STRING_PARSER)
            .setRequired(false).setShortFlag('w').setLongFlag("pswd");
        optMongoUser.setHelp("MongoDB database auth password");

        FlaggedOption optPredictor = new FlaggedOption("predictor")
            .setStringParser(JSAP.STRING_PARSER).setRequired(false).setShortFlag('p').setDefault("TF")
            .setLongFlag("predictor");
        optPredictor.setHelp("The algorithm that is used to build a model. We have [TF, POP, RAND]");

        SimpleJSAP jsap = new SimpleJSAP(ModelBuilder.class.getName(),
            "Learns user, item, context1, context2, rating model (latent "
            + "representation).", new Parameter[] { optIter, optDim, optLambda, 
            optAlpha, optPredictor, optMongoHost, optMongoPort, optMongoDBname, 
            optMongoUser, optMongoPswd });
        return jsap;
}
	
    /**
    * Takes data from the reader, builds a model, writes the data with the writer.
    * @param model_name
    */
    public void extractTransformLoad(String model_name){
        //get data
        FloatMatrix data = this.getReader().getData();

        // train the model
        predictors.get(model_name).train(data);

        // write model to databse
        List<FloatMatrix> model = predictors.get(model_name).getModel();
        System.out.println("\tGENERATED "  + model.size() + " FACTORS MATRICES");
        writers.get(model_name).writeModel(model);
    }

    public void extractTransformLoad(){
        this.extractTransformLoad("default");
    }

    public static void main(String[] args) throws JSAPException, UnknownHostException, SQLException {
        // Get current datetime as String
        Calendar cal = Calendar.getInstance();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String dt_now =  sdf.format(cal.getTime());
        // Get current PID
        String name = ManagementFactory.getRuntimeMXBean().getName();
        System.out.println("\n    >> FRAPPE TENSOR CoFi ALGORITHM - PID " + name.split("@")[0] + " @ " + dt_now + " <<");
        SimpleJSAP jsap = getProgrammOptions();
        JSAPResult jsapResult = jsap.parse(args);
        if (jsap.messagePrinted())
            System.exit(1);
		
        ModelBuilder modelBuilder = new ModelBuilder();
        modelBuilder.setReader(new MySQLDataReader(
            jsapResult.getString("host"),
            jsapResult.getInt("port"),
            jsapResult.getString("dbname"),
            jsapResult.getString("user"),
            jsapResult.getString("pswd")));
        modelBuilder.setWriter(new MySQLDataWriter(
            jsapResult.getString("host"),
            jsapResult.getInt("port"),
            jsapResult.getString("dbname"),
            jsapResult.getString("user"),
            jsapResult.getString("pswd")),
            "A");
        modelBuilder.setWriter(new MySQLDataWriter(
            jsapResult.getString("host"),
            jsapResult.getInt("port"),
            jsapResult.getString("dbname"),
            jsapResult.getString("user"),
            jsapResult.getString("pswd")),
            "B");
        //lets set the predictor
        if (jsapResult.getString("predictor").equals("TF")){
            TensorCoFi tf = new TensorCoFi(jsapResult.getInt("dim"), 
                jsapResult.getInt("nIter"),jsapResult.getFloat("lambda"), 
                jsapResult.getFloat("alpha"),
                modelBuilder.getReader().getDims());
            modelBuilder.setPred(tf, "A");
            modelBuilder.setPred(tf, "B");
        } else if (jsapResult.getString("predictor").equals("POP")) {
            PopPredictor pop = new PopPredictor();
            modelBuilder.setPred(pop);
        } else if (jsapResult.getString("predictor").equals("RAND")) {
            RandomPredictor rand = new RandomPredictor();
            modelBuilder.setPred(rand);
        } else {
            System.err.println("No such predictor implemented: "+jsapResult.getString("predictor"));
            System.exit(1);
        }
		
        //do the real job
                
        //System.out.println("    WE DISABLED MODEL A FOR TESTING!!!! ENABLE ASAP ");
        System.out.println("    -----------------------------------------------"
            + "---------------------------------");
        System.out.println("    >> PROCESSING MODEL 'A'");
        modelBuilder.extractTransformLoad("A");
        System.out.println("    -----------------------------------------------"
            + "---------------------------------");
        System.out.println("    >> PROCESSING MODEL 'B'");
            modelBuilder.extractTransformLoad("B");
	}
}
