export interface Transaction {
  date: string;
  amount: number;
  payee: string;
  source: string;
  category?: string | null;
  running_balance?: number | null;
}

export interface Subscription {
  merchant: string;
  cadence: string;
  avg_charge: number;
  last_charged: string;
  charges: number;
  annual_cost: number;
  detected_by: string;
}

export interface HealthComponentReason {
  name: string;
  weight: number;
  score: number;
  metric: string;
  ideal: string;
  explanation: string;
}

export interface HealthMetrics {
  income: number;
  expenses: number;
  net: number;
  transfers: number;
  unverified_income: number;
  monthly_expense: number;
  monthly_income: number;
  savings_rate: number;
  expense_ratio: number;
  buffer_months: number;
  runway_months: number;
  monthly_count: number;
  days_span: number;
  months_span: number;
}

export interface Health {
  score: number;
  band: string;
  components: Record<string, number>;
  metrics: HealthMetrics;
  reasoning: HealthComponentReason[];
}

export interface TimeSeriesPoint {
  date: string;
  income: number;
  expenses: number;
  net: number;
  running_balance: number;
}

export interface CategoryAgg {
  category: string;
  total: number;
  count: number;
}

export interface MonthAgg {
  month: string;
  income: number;
  expenses: number;
  net: number;
}

export interface Insight {
  type: 'warn' | 'good' | 'info';
  title: string;
  body: string;
}

export interface AnalysisResponse {
  transactions: Transaction[];
  health: Health;
  subscriptions: Subscription[];
  insights: Insight[];
  time_series: TimeSeriesPoint[];
  by_category: CategoryAgg[];
  by_month: MonthAgg[];
  top_expenses: Transaction[];
}
