import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import React from "react";

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: "#0a5d6b"
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ color, size }) => (
            <Ionicons color={typeof color === "string" ? color : undefined} name="home-outline" size={size} />
          )
        }}
      />
      <Tabs.Screen
        name="new-procedure"
        options={{
          title: "New",
          tabBarIcon: ({ color, size }) => (
            <Ionicons color={typeof color === "string" ? color : undefined} name="add-circle-outline" size={size} />
          )
        }}
      />
      <Tabs.Screen
        name="tasks"
        options={{
          title: "Tasks",
          tabBarIcon: ({ color, size }) => (
            <Ionicons color={typeof color === "string" ? color : undefined} name="list-outline" size={size} />
          )
        }}
      />
      <Tabs.Screen
        name="reports"
        options={{
          title: "Reports",
          tabBarIcon: ({ color, size }) => (
            <Ionicons
              color={typeof color === "string" ? color : undefined}
              name="document-text-outline"
              size={size}
            />
          )
        }}
      />
    </Tabs>
  );
}
