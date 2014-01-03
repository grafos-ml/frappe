

package es.tid.frappe.recsys;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Abstract class to manage SQL connection more easily.
 * 
 * @author João Baptista <joaonrb@gmail.com>
 * @since 18 Nov 2013
 */
public abstract class SQLConnection {
    
    private Connection connection;
    private Statement statement;
    
    private String host;
    private int port;
    private String db;
    private String user;
    private String password;
    
    /**
     * Constructor for the connection.
     * 
     * @param host
     *      The host name/address of the DB server.
     * @param port
     *      The port witch the DB server is listening.
     * @param dbname 
     *      The name of the DB
     * @param user 
     *      The user for authentication purposes.
     * @param pswd 
     *      The user password.
     */
    public SQLConnection(String host, int port, String dbname, String user,
            String pswd) throws SQLException {
        this.setConnection(host, port, dbname, user, pswd);
    }
    
    /**
     * Close the connection and statement
     * @throws SQLException 
     */
    private void close() throws SQLException {
        if(this.statement != null)
            this.statement.close();
        if(this.connection != null)
            this.connection.close();
    }
    
    /**
     * Close any open connection before dispose this.
     * @throws Exception
     * @throws Throwable 
     */
    public void finalize() throws Exception, Throwable{
        this.close();
        super.finalize();
        
    }
    
    /**
     * Sets the connection or prepare this to connect to the db.
     * 
     * @param host
     *      The database server host.
     * @param port
     *      The data base server port.
     * @param dbname
     *      The database server name.
     * @param user
     *      The database username for authenticate in the DBMS.
     * @param pswd
     *      The user password for authentication purposes.
     */
    public void setConnection(String host, int port, String dbname, String user,
            String pswd) throws SQLException {
        this.close();
        this.host = host;
        this.port = port;
        this.db = dbname;
        this.user = user;
        this.password = pswd;
        this.connection = null;
    }
    
    /**
     * Build the database url.
     * 
     * @return
     *      The database url
     */
    public String getUrl() {
        return String.format("jdbc:mysql://%s:%d/%s",this.host,this.port,this.db);
    }
    
    /**
     * Execute a query a return a result set for consult.
     * 
     * @param query
     *      The query to be executed. Must be SQL standard or SQL specific of
     *      the DBMS implementing this.
     * @return
     *      A result set of the query.
     * @throws SQLException
     *      SQL related errors provoke this. Make sure to use it correctly.
     */
    public ResultSet executeQuery(String query) throws SQLException {
        try {
            Class.forName("com.mysql.jdbc.Driver").newInstance();
        } catch (ClassNotFoundException | InstantiationException | IllegalAccessException ex) {
            Logger.getLogger(SQLConnection.class.getName()).log(Level.SEVERE, null, ex);
        }
        //System.out.println(this.getUrl());
        if(this.connection == null)
            this.connection = DriverManager.getConnection(this.getUrl(),
                    this.user,this.password);
        this.statement = this.connection.createStatement();
        return this.statement.executeQuery(query);
    }
    
    /**
     * Execute an update .
     * 
     * @param query
     *      The query with data to update. Must be SQL standard or SQL specific
     *      of the DBMS implementing this.
     * @return
     *      True if the insertion was a success.
     * @throws SQLException
     *      SQL related errors provoke this. Make sure to use it correctly.
     */
    public boolean executeUpdate(String query) throws SQLException {
        try {
            Class.forName("com.mysql.jdbc.Driver").newInstance();
        } catch (ClassNotFoundException | InstantiationException | IllegalAccessException ex) {
            Logger.getLogger(SQLConnection.class.getName()).log(Level.SEVERE, null, ex);
        }
        //System.out.println(this.getUrl());
        if(this.connection == null)
            this.connection = DriverManager.getConnection(this.getUrl(),
                    this.user,this.password);
        this.statement = this.connection.createStatement();
        return this.statement.executeUpdate(query) == 1;
    }
}
