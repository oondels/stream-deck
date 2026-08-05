//  Subscribe to MakeVonMatteo on tiktok :)

// Key definitions
#define BUTTON_KEY1 KEY_F13
#define BUTTON_KEY2 KEY_F14
#define BUTTON_KEY3 KEY_F15
#define BUTTON_KEY4 KEY_F16
#define BUTTON_KEY5 KEY_F17
#define BUTTON_KEY6 KEY_F18
#define BUTTON_KEY7 KEY_F19
#define BUTTON_KEY8 KEY_F20
#define BUTTON_KEY9 KEY_F21
#define BUTTON_KEY10 KEY_F22

// Pin definitions
#define BUTTON_PIN1 2
#define BUTTON_PIN2 3
#define BUTTON_PIN3 4
#define BUTTON_PIN4 5
#define BUTTON_PIN5 6
#define BUTTON_PIN6 7
#define BUTTON_PIN7 8
#define BUTTON_PIN8 9
#define BUTTON_PIN9 10
#define BUTTON_PIN10 16

#define LED_STRIP_PIN 13  // Corresponds to D15 (physical)
#define NUM_LEDS 11

#include <Keyboard.h>
#include <Adafruit_NeoPixel.h>

Adafruit_NeoPixel strip(NUM_LEDS, LED_STRIP_PIN, NEO_GRB + NEO_KHZ800);

// LED colors
uint32_t normalColor = strip.Color(0, 150, 255); // Light blue
uint32_t pressColor  = strip.Color(0, 0, 150);   // Dark blue

class button {
 public:
   const char key;
   const uint8_t pin;

   button(uint8_t k, uint8_t p) : key(k), pin(p) {}

   void press(boolean state) {
     if (state == pressed || (millis() - lastPressed <= debounceTime)) {
       return;
     }

     lastPressed = millis();
     state ? Keyboard.press(key) : Keyboard.release(key);
     pressed = state;
   }

   void update() {
     press(!digitalRead(pin));
   }

   boolean isPressed() {
     return pressed;
   }

 private:
   const unsigned long debounceTime = 30;
   unsigned long lastPressed = 0;
   boolean pressed = 0;
};

// Button initialization
button buttons[] = {
 button(BUTTON_KEY1, BUTTON_PIN1),
 button(BUTTON_KEY2, BUTTON_PIN2),
 button(BUTTON_KEY3, BUTTON_PIN3),
 button(BUTTON_KEY4, BUTTON_PIN4),
 button(BUTTON_KEY5, BUTTON_PIN5),
 button(BUTTON_KEY6, BUTTON_PIN6),
 button(BUTTON_KEY7, BUTTON_PIN7),
 button(BUTTON_KEY8, BUTTON_PIN8),
 button(BUTTON_KEY9, BUTTON_PIN9),
 button(BUTTON_KEY10, BUTTON_PIN10)
};

#define NumButtons (sizeof(buttons) / sizeof(buttons[0]))

void setup() {
 // LED initialization
 strip.begin();
 strip.show(); // Make sure the LEDs are off at the start
 
 // Button initialization
 for (int i = 0; i < NumButtons; i++) {
   pinMode(buttons[i].pin, INPUT_PULLUP); // Set to input mode with pull-up for each button
 }

 // Keyboard initialization
 Keyboard.begin();
}

void loop() {
 boolean anyPressed = false;

 // Update button states and check if any of them are pressed
 for (int i = 0; i < NumButtons; i++) {
   buttons[i].update();
   if (buttons[i].isPressed()) {
     anyPressed = true;
   }
 }

 // If a button is pressed, change LED color to dark blue
 if (anyPressed) {
   setAllLEDs(pressColor);
 } else {
   setAllLEDs(normalColor);
 }
}

// Function to change the color of all LEDs
void setAllLEDs(uint32_t color) {
 for (int i = 0; i < strip.numPixels(); i++) {
   strip.setPixelColor(i, color);
 }
 strip.show(); // Update the LEDs
}

 