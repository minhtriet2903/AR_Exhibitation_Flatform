package com.example.visitor;

import androidx.appcompat.app.AppCompatActivity;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.os.SystemClock;
import android.util.Log;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.ObjectInputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.UnknownHostException;
// We need to use this Handler package
import android.os.Handler;

// Create the Handler object (on the main thread by default)


public class MainActivity extends AppCompatActivity {

    EditText message;
    Socket socket;
    TextView viewText;

    private static final int SERVERPORT = 8080;
    private static final String SERVER_IP = "10.0.2.2";

    Handler handler = new Handler();
    // Define the code block to be executed
    private Runnable runnableCode = new Runnable() {
        @Override
        public void run() {
            // Do something here on the main thread
            Log.d("Handlers", "Called on main thread");
            handler.postDelayed(runnableCode, 2000);
        }
    };
        // Run the above code block on the main thread after 2 seconds


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        message = (EditText) findViewById(R.id.inputMessage);
        viewText =(TextView) findViewById(R.id.textView);

        AlarmManager alarmManager =
                (AlarmManager) this.getSystemService(Context.ALARM_SERVICE);

        Intent intent = new Intent(this, AlarmReceiver.class);

        PendingIntent pendingIntent =
                PendingIntent.getBroadcast(this, 0, intent, 0);
        if (pendingIntent != null && alarmManager != null) {
            alarmManager.cancel(pendingIntent);
        }
        alarmManager.setInexactRepeating(AlarmManager.ELAPSED_REALTIME_WAKEUP,
                SystemClock.elapsedRealtime() +
                        1000,1000, pendingIntent);
    }

    public void send(View view) {
        String mess  = message.getText().toString();
//        SendMessage sendMess = new SendMessage();
//        sendMess.execute(mess);
        Toast.makeText(MainActivity.this, "Sent "+mess, Toast.LENGTH_SHORT).show();
        // Start the initial runnable task by posting through the handler
        handler.post(runnableCode);
    }

    public class SendMessage extends AsyncTask<String, Void, Void> {
        InputStreamReader inputStreamReader ;
        BufferedReader bufferedReader ;
        Handler handler = new Handler();
        String message;
        @Override
        protected Void doInBackground(String... voids) {
            try {
                socket = new Socket("10.0.2.2", 8080);
                PrintWriter outToServer = new PrintWriter(
                        new OutputStreamWriter(socket.getOutputStream())
                );
                outToServer.write(voids[0]);
                outToServer.flush();

                inputStreamReader = new InputStreamReader(socket.getInputStream());
                bufferedReader = new BufferedReader(inputStreamReader);
                message = bufferedReader.readLine();
                handler.post(new Runnable() {
                    @Override
                    public void run() {
                        Toast.makeText(getApplicationContext(), "receive "+message, Toast.LENGTH_SHORT).show();
                    }
                });

                outToServer.close();
                socket.close();
            } catch (IOException e){
                e.printStackTrace();
            }
            return null;
        }
    }
}