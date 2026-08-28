import type { ComponentProps } from "react";
import { Link } from "expo-router";
import { Text, View } from "react-native";

// Expo Router and the React Native 0.87 web typing surface disagree on registered style objects.
export function asLinkStyle(style: unknown): ComponentProps<typeof Link>["style"] {
  return style as ComponentProps<typeof Link>["style"];
}

export function asTextStyle(style: unknown): ComponentProps<typeof Text>["style"] {
  return style as ComponentProps<typeof Text>["style"];
}

export function asViewStyle(style: unknown): ComponentProps<typeof View>["style"] {
  return style as ComponentProps<typeof View>["style"];
}
