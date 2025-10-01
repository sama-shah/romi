#define RT0 10000   // Reference resistance
#define B 3977      // Beta coefficient
#define VCC 5       // Supply voltage
#define R 10000     // Series resistor

float RT, VR, ln, TX, T0, VRT;

void setup() {
  pinMode(A0, INPUT); // Thermistor pin
  pinMode(A5, INPUT); // Heartbeat sensor pin
  Serial.begin(9600);
  T0 = 25 + 273.15;   // Reference temperature in Kelvin
}

void loop() {
  // ---------- TEMPERATURE CALCULATION ----------
  VRT = analogRead(A0);                  // Read thermistor voltage
  VRT = (5.00 / 1023.00) * VRT;          // Convert to voltage
  VR = VCC - VRT;
  RT = R * (VCC - VRT) / VRT;            // Calculate resistance
  ln = log(RT / RT0);
  TX = (1 / ((ln / B) + (1 / T0)));      // Calculate temperature in Kelvin
  TX = TX - 273.15;                      // Convert to Celsius

  // ---------- HEARTBEAT READING ----------
  float pulse;
  int sum = 0;
  for (int i = 0; i < 20; i++) {
    sum += analogRead(A5);              // Average to smooth noise
  }
  pulse = sum / 20.0;

  // ---------- SERIAL PLOT OUTPUT ----------
  // Only numbers separated by spaces:
  Serial.print(TX);       // Temperature in Celsius
  Serial.print(" ");
  Serial.println(pulse);  // Heartbeat value

  delay(100);  // Update speed (~10 samples/sec)
}
