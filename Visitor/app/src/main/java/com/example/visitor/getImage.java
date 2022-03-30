package com.example.visitor;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.Handler;
import android.provider.MediaStore;
import android.util.Base64;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.Toast;

import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.Socket;

public class getImage extends AppCompatActivity {

    ImageView imageView;
    ImageView imageBack;
    Button btnPick;
    Socket socket;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_get_image);
        imageView = (ImageView) findViewById(R.id.imageView);
        imageBack = (ImageView) findViewById(R.id.imageFromServer);

        btnPick = (Button) findViewById(R.id.button2);

        btnPick.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                dispatchTakePictureIntent();
            }
        });
    }

    static final int REQUEST_IMAGE_CAPTURE = 1;

    private void dispatchTakePictureIntent() {
        Intent takePictureIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
        try {
            startActivityForResult(takePictureIntent, REQUEST_IMAGE_CAPTURE);
        } catch (ActivityNotFoundException e) {
            // display error state to the user
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_IMAGE_CAPTURE && resultCode == RESULT_OK) {
            Bundle extras = data.getExtras();
            Bitmap imageBitmap = (Bitmap) extras.get("data");
            imageView.setImageBitmap(imageBitmap);

            getImage.SendMessage sendMess = new getImage.SendMessage();
            sendMess.execute(imageBitmap);
//            Toast.makeText(getImage.this, "Sent ", Toast.LENGTH_SHORT).show();

        }
    }

    public class SendMessage extends AsyncTask<Bitmap, Void, Void> {
        InputStreamReader inputStreamReader;
        BufferedReader bufferedReader;
        Handler handler = new Handler();
        String message;

        @Override
        protected Void doInBackground(Bitmap... voids) {
            try {
                socket = new Socket("192.168.1.8", 8080);
                PrintWriter outToServer = new PrintWriter(
                        new OutputStreamWriter(socket.getOutputStream())
                );


                ByteArrayOutputStream baos = new ByteArrayOutputStream();
                voids[0].compress(Bitmap.CompressFormat.JPEG, 100, baos);
                byte array[] = baos.toByteArray();

                //send photo to server
                OutputStream out = socket.getOutputStream();
                DataOutputStream dos = new DataOutputStream(out);
                dos.write(array, 0, array.length);
                dos.flush();

                PrintWriter out_done_signal = new PrintWriter(
                        new OutputStreamWriter(socket.getOutputStream())
                );
                out_done_signal.write("done");
                outToServer.flush();

                // get image back from server
                DataInputStream dis;
                try {
                    dis=new DataInputStream(socket.getInputStream());

                    int bytesRead;
                    byte[] pic = new byte[5000*1024];
                    bytesRead = dis.read(pic, 0, pic.length);
                    Bitmap imageBackData;
                    imageBackData = BitmapFactory.decodeByteArray(pic, 0, bytesRead);
                    imageBack.setImageBitmap(imageBackData);

                } catch(Exception e) {
                    Log.e("TCP", "S: Error", e);
                }
                outToServer.close();
                socket.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
            return null;
        }
    }
}