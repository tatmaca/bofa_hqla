import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  ScrollView,
  RefreshControl,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  Alert
} from 'react-native';
import { LineChart, BarChart } from 'react-native-chart-kit';
import { Dimensions } from 'react-native';
import * as Notifications from 'expo-notifications';

// API base URL - update this to your server
const API_BASE = 'http://10.0.0.13:8888'; // Your computer's IP address

const screenWidth = Dimensions.get('window').width;

export default function App() {
  const [date, setDate] = useState('');
  const [dates, setDates] = useState([]);
  const [curveData, setCurveData] = useState(null);
  const [stats, setStats] = useState(null);
  const [news, setNews] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInitialData();
    setupNotifications();
  }, []);

  useEffect(() => {
    if (date) {
      loadData(date);
    }
  }, [date]);

  const setupNotifications = async () => {
    const { status } = await Notifications.requestPermissionsAsync();
    if (status === 'granted') {
      // Schedule daily notification for pipeline updates
      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'Yield Curve Update',
          body: 'New yield curve data available',
        },
        trigger: { hour: 17, minute: 0, repeats: true }, // 5 PM daily
      });
    }
  };

  const loadInitialData = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/dates`);
      const data = await response.json();
      setDates(data.dates || []);
      if (data.dates && data.dates.length > 0) {
        setDate(data.dates[0]);
      }
    } catch (error) {
      console.error('Error loading dates:', error);
      Alert.alert('Error', 'Could not connect to server. Make sure the dashboard is running.');
      setLoading(false);
    }
  };

  const loadData = async (selectedDate) => {
    setLoading(true);
    try {
      const [curveRes, statsRes, newsRes] = await Promise.all([
        fetch(`${API_BASE}/api/curve/${selectedDate}`),
        fetch(`${API_BASE}/api/stats/${selectedDate}`),
        fetch(`${API_BASE}/api/news/top/${selectedDate}?limit=5`)
      ]);

      const curve = await curveRes.json();
      const statsData = await statsRes.json();
      const newsData = await newsRes.json();

      setCurveData(curve);
      setStats(statsData);
      setNews(newsData.articles || []);
    } catch (error) {
      console.error('Error loading data:', error);
      Alert.alert('Error', 'Failed to load data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadInitialData();
    if (date) {
      loadData(date);
    }
  };

  const formatChange = (value) => {
    if (value === 0) return '0.0 bps';
    const sign = value > 0 ? '+' : '';
    return `${sign}${value.toFixed(1)} bps`;
  };

  const getChangeColor = (value) => {
    if (value > 0) return '#e74c3c';
    if (value < 0) return '#27ae60';
    return '#7f8c8d';
  };

  if (loading && !curveData) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!curveData) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.errorText}>No data available</Text>
          <TouchableOpacity style={styles.button} onPress={onRefresh}>
            <Text style={styles.buttonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const tenors = ['6m', '1y', '2y', '3y', '5y', '7y', '10y', '20y', '30y'];
  const todayYields = tenors.map(t => curveData.today.zeros_pct[t] || 0);
  const prevYields = tenors.map(t => curveData.prev_day.zeros_pct[t] || 0);
  const deltas = tenors.map(t => (curveData.delta.zeros_pct[t] || 0) * 100);

  const chartConfig = {
    backgroundColor: '#ffffff',
    backgroundGradientFrom: '#ffffff',
    backgroundGradientTo: '#ffffff',
    decimalPlaces: 2,
    color: (opacity = 1) => `rgba(102, 126, 234, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
    style: {
      borderRadius: 16
    },
    propsForDots: {
      r: '4',
      strokeWidth: '2',
      stroke: '#667eea'
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.header}>
          <Text style={styles.title}>Yield Curve</Text>
          <Text style={styles.date}>{date}</Text>
        </View>

        {/* Stats Cards */}
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>2Y</Text>
            <Text style={styles.statValue}>
              {stats?.yields['2y']?.toFixed(2) || '-'}%
            </Text>
            <Text style={[styles.statChange, { color: getChangeColor(stats?.changes_bps['2y'] || 0) }]}>
              {stats?.changes_bps['2y'] ? formatChange(stats.changes_bps['2y']) : '-'}
            </Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>10Y</Text>
            <Text style={styles.statValue}>
              {stats?.yields['10y']?.toFixed(2) || '-'}%
            </Text>
            <Text style={[styles.statChange, { color: getChangeColor(stats?.changes_bps['10y'] || 0) }]}>
              {stats?.changes_bps['10y'] ? formatChange(stats.changes_bps['10y']) : '-'}
            </Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>30Y</Text>
            <Text style={styles.statValue}>
              {stats?.yields['30y']?.toFixed(2) || '-'}%
            </Text>
            <Text style={[styles.statChange, { color: getChangeColor(stats?.changes_bps['30y'] || 0) }]}>
              {stats?.changes_bps['30y'] ? formatChange(stats.changes_bps['30y']) : '-'}
            </Text>
          </View>
        </View>

        {/* Yield Curve Chart */}
        <View style={styles.chartContainer}>
          <Text style={styles.chartTitle}>Yield Curve: Today vs Yesterday</Text>
          <LineChart
            data={{
              labels: tenors,
              datasets: [
                {
                  data: todayYields,
                  color: (opacity = 1) => `rgba(102, 126, 234, ${opacity})`,
                  strokeWidth: 2
                },
                {
                  data: prevYields,
                  color: (opacity = 1) => `rgba(150, 150, 150, ${opacity})`,
                  strokeWidth: 2
                }
              ],
              legend: [curveData.as_of, curveData.prev]
            }}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
          />
        </View>

        {/* Delta Chart */}
        <View style={styles.chartContainer}>
          <Text style={styles.chartTitle}>Day-over-Day Changes</Text>
          <BarChart
            data={{
              labels: tenors,
              datasets: [{
                data: deltas
              }]
            }}
            width={screenWidth - 40}
            height={220}
            chartConfig={{
              ...chartConfig,
              color: (opacity = 1, index) => {
                const value = deltas[index];
                return value >= 0 
                  ? `rgba(231, 76, 60, ${opacity})` 
                  : `rgba(39, 174, 96, ${opacity})`;
              }
            }}
            style={styles.chart}
            showValuesOnTopOfBars
          />
        </View>

        {/* Top News */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Top News Articles</Text>
          {news.map((article, index) => (
            <TouchableOpacity key={index} style={styles.newsItem}>
              <Text style={styles.newsTitle}>{article.title}</Text>
              <Text style={styles.newsSource}>{article.source} • {article.bucket}</Text>
              {article.summary && (
                <Text style={styles.newsSummary} numberOfLines={2}>
                  {article.summary}
                </Text>
              )}
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 18,
    color: '#666',
  },
  errorText: {
    fontSize: 18,
    color: '#e74c3c',
    marginBottom: 20,
  },
  button: {
    backgroundColor: '#667eea',
    paddingHorizontal: 30,
    paddingVertical: 12,
    borderRadius: 8,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    backgroundColor: '#667eea',
    padding: 20,
    paddingTop: 10,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: 'white',
    marginBottom: 5,
  },
  date: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  statsRow: {
    flexDirection: 'row',
    padding: 15,
    backgroundColor: 'white',
    marginTop: 10,
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
    padding: 10,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
    fontWeight: '600',
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#333',
    marginBottom: 5,
  },
  statChange: {
    fontSize: 12,
    fontWeight: '600',
  },
  chartContainer: {
    backgroundColor: 'white',
    margin: 10,
    padding: 15,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 10,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  section: {
    backgroundColor: 'white',
    margin: 10,
    padding: 15,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#667eea',
    marginBottom: 15,
  },
  newsItem: {
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  newsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 5,
  },
  newsSource: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
  },
  newsSummary: {
    fontSize: 14,
    color: '#555',
    lineHeight: 20,
  },
});

