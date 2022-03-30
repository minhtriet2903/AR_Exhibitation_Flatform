package com.example.visitor;

import android.os.AsyncTask;

import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.Socket;

public class MessageSender extends AsyncTask<String, Void, Void> {
    @Override
    protected Void doInBackground(String... voids) {
        try {
            Socket s = new Socket("192.168.1.8", 8080);
            PrintWriter outToServer = new PrintWriter(
                    new OutputStreamWriter(s.getOutputStream())
            );
            outToServer.write(voids[0]+ "\r\n");
            outToServer.flush();
            outToServer.close();
            s.close();
        } catch (IOException e){
            e.printStackTrace();
        }
        return null;
    }
}
