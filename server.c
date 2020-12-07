#include "Servo.h"
#include "LibPrintf.h"

const int number_servos = 4;
Servo servo[number_servos];

int pot_val[number_servos];
int pot_angle[number_servos] = {90, 90, 140, 0};

void setup() {
  Serial.begin(115200);

  int ports[4] = {2, 3, 4, 5};
  
  for (int i = 0; i < number_servos; ++i) {
    servo[i].attach(ports[i]);
    servo[i].write(pot_angle[i]);
    delay(200);
  }

  printf("Executed, current state: %d %d %d %d\n", pot_angle[0], pot_angle[1], pot_angle[2], pot_angle[3]);
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    printf("Received command: %c\n", command);

    if (command == 'S') {
      for (int i = 0; i < number_servos; ++i)
        servo_saved[i][saved_positions] = pot_angle[i];
      
      saved_positions += 1;
      printf("Position %d saved\n", saved_positions);
      delay(1500);
    } else if (command == 'P') {
      for (int i = 0; i < saved_positions; ++i)
        for (int j = 0; j < number_servos; ++j) {
          servo[j].write(servo_saved[j][i]);
          delay(500);
        }
       
      printf("Executed sequence of %d positions.\n", saved_positions);
      delay(2000);
    } else if (command == 'R') {
      saved_positions = 0;
      printf("Removed saved moves.\n");
    } else if (command >= 'A' && command <= 'D') {
      int value = Serial.parseInt();
      int diff = value - pot_angle[command - 'A'];

      for (int i = 0; abs(i) <= abs(diff); i += (diff > 0 ? 1 : -1)) {
        servo[command - 'A'].write(pot_angle[command - 'A'] + i);
        delay(10);
      }

      pot_angle[command - 'A'] = value;
      printf("Executed, current state: %d %d %d %d\n", pot_angle[0], pot_angle[1], pot_angle[2], pot_angle[3]);
    } else if (command == 'E') {
      
    } else {
      printf("Command unknown.\n");
    }
  }
}
