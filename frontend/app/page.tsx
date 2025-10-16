"use client";

import { useState, useEffect } from 'react';

// Define a type for our alert data for type safety
interface FraudAlert {
  type: string;
  reason: string;
  transaction: {
    user_id: string;
    card_id: string;
    device_id: string;
    amount: number;
    merchant: string;
  };
}

// In a real app, this would come from an environment variable
// Pointing to the backend's WebSocket endpoint
const WS_URL = "ws://localhost:8000/ws";

export default function Home() {
  const [alerts, setAlerts] = useState<FraudAlert[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<string>('Connecting...');

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: NodeJS.Timeout;

    const connect = () => {
      try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
          console.log('Successfully connected to WebSocket server!');
          setConnectionStatus('Connected');
        };

        ws.onmessage = (event) => {
          console.log('Received alert:', event.data);
          try {
            const newAlert: FraudAlert = JSON.parse(event.data);
            // Add new alerts to the top of the list for visibility
            setAlerts(prevAlerts => [newAlert, ...prevAlerts]);
          } catch (error) {
            console.error("Failed to parse alert data:", error);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setConnectionStatus('Error');
        };

        ws.onclose = () => {
          console.log('Disconnected from WebSocket server.');
          setConnectionStatus('Disconnected - Reconnecting...');
          // Attempt to reconnect after 3 seconds
          reconnectTimer = setTimeout(() => {
            connect();
          }, 3000);
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        setConnectionStatus('Failed to connect');
      }
    };

    connect();

    // Cleanup function to close the socket when the component unmounts
    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) {
        ws.close();
      }
    };
  }, []); // The empty dependency array ensures this runs only once

  return (
    <main className="flex min-h-screen flex-col items-center p-12 bg-gray-900 text-white">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-8 text-center text-red-400">
          Project Phoenix: Live Fraud Alerts
        </h1>
        <div className="bg-gray-800 rounded-lg shadow-xl p-6">
          <div className="flex justify-between items-center mb-4 border-b border-gray-600 pb-2">
            <h2 className="text-xl font-semibold">Incoming Alerts</h2>
            <div className="flex items-center gap-4">
              <span className={`text-sm ${connectionStatus === 'Connected' ? 'text-green-400' : 'text-yellow-400'}`}>
                {connectionStatus}
              </span>
              <span className="text-gray-400">{alerts.length} Total</span>
            </div>
          </div>
          <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
            {alerts.length === 0 ? (
              <p className="text-gray-500 text-center py-8">Awaiting transaction data...</p>
            ) : (
              alerts.map((alert, index) => (
                <div key={index} className="bg-gray-700 p-4 rounded-md border-l-4 border-red-500 animate-fade-in">
                  <p className="font-bold text-red-400 text-lg">{alert.reason}</p>
                  <div className="text-sm text-gray-300 mt-2 grid grid-cols-2 gap-x-4">
                    <p><strong>User:</strong> {alert.transaction.user_id}</p>
                    <p><strong>Amount:</strong> ${alert.transaction.amount.toFixed(2)}</p>
                    <p><strong>Card:</strong> {alert.transaction.card_id}</p>
                    <p><strong>Merchant:</strong> {alert.transaction.merchant}</p>
                    <p className="col-span-2"><strong>Device:</strong> {alert.transaction.device_id}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </main>
  );
}