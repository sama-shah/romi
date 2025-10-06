import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';

import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import 'react-native-reanimated';
import { useColorScheme } from 'react-native';

export const unstable_settings = {
  anchor: '(tabs)',
};

export default function RootLayout() {
  const colorScheme = useColorScheme();

  /* 
  APP SETUP: 
  Global boolean to check if set up:

  if setup boolean == false:
    - user flow: 
      1. Welcome!
      2. Personalization (name, age, typical cycle length)
      3. Goals (for insights feedback)
      4. Bluetooth connection to romi band 
  
  if setup boolean == true:
  navigate to Stack.Screen name="(tabs)"
  */

  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      </Stack>
      <StatusBar style="auto" />
    </ThemeProvider>
  );
}
