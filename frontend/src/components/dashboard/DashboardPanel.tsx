"use client";

import { useState, useEffect } from "react";
import { API_URL } from "@/lib/constants";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { BarChart3, TrendingUp, TrendingDown, Hotel, Users, Globe, AlertTriangle, ArrowLeft, ChevronDown } from "lucide-react";
import TimeSeriesChart from "@/components/charts/TimeSeriesChart";

interface DashboardPanelProps {
  summary: any;
  loading: boolean;
  selectedYear: number;
  onYearChange: (year: number) => void;
  selectedGovId: number | null;
  onGovSelect: (id: number | null) => void;
}

export default function DashboardPanel({
  summary, loading, selectedYear, onYearChange, selectedGovId, onGovSelect,
}: DashboardPanelProps) {
  const [govDetail, setGovDetail] = useState<any>(null);
  const [destinationType, setDestinationType] = useState("");

  useEffect(() => {
    if (selectedGovId) {
      fetch(`${API_URL}/api/summary/governorate/${selectedGovId}?year=${selectedYear}`)
        .then(r => r.json())
        .then(setGovDetail)
        .catch(console.error);
    } else {
      setGovDetail(null);
    }
  }, [selectedGovId, selectedYear]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground text-sm">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Filters */}
      <div className="flex gap-2">
        <div className="flex-1">
          <label className="text-[10px] text-muted-foreground uppercase tracking-wider">Year</label>
          <select
            value={selectedYear}
            onChange={(e) => onYearChange(Number(e.target.value))}
            className="w-full mt-1 h-8 rounded-md border border-input bg-secondary px-2 text-sm text-foreground"
          >
            {[2025, 2024, 2023, 2022, 2021, 2020].map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
        <div className="flex-1">
          <label className="text-[10px] text-muted-foreground uppercase tracking-wider">Type</label>
          <select
            value={destinationType}
            onChange={(e) => setDestinationType(e.target.value)}
            className="w-full mt-1 h-8 rounded-md border border-input bg-secondary px-2 text-sm text-foreground"
          >
            <option value="">All</option>
            <option value="archaeological">Cultural</option>
            <option value="natural">Nature</option>
            <option value="coastal">Coastal</option>
            <option value="religious">Religious</option>
          </select>
        </div>
      </div>

      {/* National Overview */}
      {!selectedGovId && summary && (
        <>
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 className="w-4 h-4 text-primary" />
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">National Overview</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <StatCard icon={<Users className="w-3.5 h-3.5" />} label="Visitors" value={fmt(summary.total_visitors)} />
            <StatCard icon={<Globe className="w-3.5 h-3.5" />} label="International" value={`${fmt(summary.international_visitors)}`} sub={`${(summary.international_visitors / summary.total_visitors * 100).toFixed(0)}%`} />
            <StatCard icon={<Hotel className="w-3.5 h-3.5" />} label="Hotels" value={summary.total_hotels.toString()} />
            <StatCard icon={<BarChart3 className="w-3.5 h-3.5" />} label="Rooms" value={fmt(summary.total_rooms)} />
          </div>

          <Card>
            <CardContent className="pt-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-muted-foreground">Avg Occupancy</span>
                <Badge variant={summary.avg_occupancy_rate > 60 ? "warning" : "secondary"}>
                  {summary.avg_occupancy_rate}%
                </Badge>
              </div>
              <Progress value={summary.avg_occupancy_rate} max={100} />
            </CardContent>
          </Card>

          {summary.high_priority_zones > 0 && (
            <Card className="border-destructive/50">
              <CardContent className="pt-4 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-destructive" />
                <span className="text-xs">
                  <strong className="text-destructive">{summary.high_priority_zones}</strong> high-priority zones need investment
                </span>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Governorate Detail */}
      {govDetail && selectedGovId && (
        <>
          <Button variant="ghost" size="sm" onClick={() => onGovSelect(null)} className="text-primary -ml-2">
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to National
          </Button>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">{govDetail.governorate.name_en}</CardTitle>
              <div className="text-xs text-muted-foreground">{govDetail.governorate.name_ar}</div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <MiniStat label="Population" value={fmt(govDetail.governorate.population)} />
                <MiniStat label="Area" value={`${fmt(govDetail.governorate.area_km2)} km²`} />
                <MiniStat label="Hotels" value={govDetail.accommodation.hotel_count.toString()} />
                <MiniStat label="Rooms" value={fmt(govDetail.accommodation.total_rooms)} />
              </div>

              <Separator />

              {govDetail.visitors.length > 0 && (
                <div>
                  <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">Visitor Trend</div>
                  <TimeSeriesChart
                    data={govDetail.visitors}
                    title=""
                    color="var(--primary)"
                    height={120}
                  />
                </div>
              )}

              {govDetail.occupancy.length > 0 && (
                <div>
                  <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">Occupancy</div>
                  <TimeSeriesChart
                    data={govDetail.occupancy.map((o: any) => ({ year: o.year, month: o.month, total: o.rate }))}
                    title=""
                    color="#22c55e"
                    height={120}
                  />
                </div>
              )}

              {govDetail.indicators && (
                <>
                  <Separator />
                  <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">Capacity Indicators</div>

                  {govDetail.indicators.capacity_classification && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">Classification</span>
                      <Badge variant={
                        govDetail.indicators.capacity_classification === "under" ? "destructive" :
                        govDetail.indicators.capacity_classification === "over" ? "warning" : "success"
                      }>
                        {govDetail.indicators.capacity_classification.toUpperCase()}
                      </Badge>
                    </div>
                  )}

                  {govDetail.indicators.priority_score !== null && (
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-xs text-muted-foreground">Priority Score</span>
                        <span className="text-xs font-semibold text-primary">{govDetail.indicators.priority_score.toFixed(1)}</span>
                      </div>
                      <Progress value={govDetail.indicators.priority_score} max={100} />
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function StatCard({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string; sub?: string }) {
  return (
    <Card>
      <CardContent className="pt-3 pb-3">
        <div className="flex items-center gap-1.5 mb-1">
          <span className="text-muted-foreground">{icon}</span>
          <span className="text-[10px] text-muted-foreground uppercase">{label}</span>
        </div>
        <div className="text-lg font-semibold text-foreground">{value}</div>
        {sub && <div className="text-[10px] text-muted-foreground">{sub}</div>}
      </CardContent>
    </Card>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-secondary rounded-md p-2">
      <div className="text-[10px] text-muted-foreground">{label}</div>
      <div className="text-sm font-semibold text-foreground">{value}</div>
    </div>
  );
}

function fmt(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n.toLocaleString();
}
