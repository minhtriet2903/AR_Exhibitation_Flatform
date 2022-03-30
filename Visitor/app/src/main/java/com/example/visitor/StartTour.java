package com.example.visitor;

import java.util.TimerTask;

public class StartTour  extends TimerTask {
        @Override
        public void run() {
            Camera2API camera = new Camera2API();
            camera.takePicture();
        }
}
