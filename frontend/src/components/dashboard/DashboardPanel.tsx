"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { API_URL } from "@/lib/constants";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart3, Users, Globe, Hotel, AlertTriangle, ArrowLeft } from "lucide-react";
import TimeSeriesChart from "@/components/charts/TimeSeriesChart";

interface DashboardPanelProps {
  summary: any;
  loading: boolean;
  selectedYear: number;
  onYearChange: (year: number) => void;
  selectedGovId: number | null;
  onGovSelect: (id: number | null) => void;
}

const container = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.06 },
  },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 120, damping: 14 } },
};

function fmt(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n.toLocaleString();
}

function StatCard({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string; sub?: string }) {
  return (
    <motion.div variants={item} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
      <Card className="bg-card border-border/60 hover:border-primary/40 transition-colors cursor-pointer">
        <CardContent className="pt-3 pb-3">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-muted-foreground">{icon}</span>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</span>
          </div>
          <div className="text-lg font-semibold text-foreground">{value}</div>
          {sub && <div className="text-[10px] text-muted-foreground">{sub}</div>}
        </CardContent>
      </Card>
    </motion.div>
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

function DashboardSkeleton() {
  return (
    <div className="p-4 space-y-4">
      {/* Filters skeleton */}
      <div className="flex gap-2">
        <div className="flex-1 space-y-1.5">
          <Skeleton className="h-3 w-12" />
          <Skeleton className="h-8 w-full" />
        </div>
        <div className="flex-1 space-y-1.5">
          <Skeleton className="h-3 w-12" />
          <Skeleton className="h-8 w-full" />
        </div>
      </div>

      {/* Section label */}
      <Skeleton className="h-3 w-28" />

      {/* Stat cards skeleton */}
      <motion.div
        className="grid grid-cols-2 gap-2"
        variants={container}
        initial="hidden"
        animate="show"
      >
        {[...Array(4)].map((_, i) => (
          <motion.div key={i} variants={item}>
            <Card className="bg-card border-border/60">
              <CardContent className="pt-3 pb-3 space-y-2">
                <div className="flex items-center gap-1.5">
                  <Skeleton className="h-3.5 w-3.5 rounded" />
                  <Skeleton className="h-3 w-16" />
                </div>
                <Skeleton className="h-6 w-20" />
                <Skeleton className="h-3 w-12" />
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {/* Occupancy card skeleton */}
      <Card className="bg-card border-border/60">
        <CardContent className="pt-4 space-y-3">
          <div className="flex justify-between">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-5 w-12" />
          </div>
          <Skeleton className="h-2 w-full rounded-full" />
        </CardContent>
      </Card>
    </div>
  );
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

  if (loading) return <DashboardSkeleton />;

  return (
    <motion.div
      className="p-4 space-y-4"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Filters */}
      <div className="flex gap-2">
        <div className="flex-1">
          <label className="text-[10px] text-muted-foreground uppercase tracking-wider">Year</label>
          <select
            value={selectedYear}
            onChange={(e) => onYearChange(Number(e.target.value))}
            className="w-full mt-1 h-8 rounded-md border border-input bg-secondary px-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
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
            className="w-full mt-1 h-8 rounded-md border border-input bg-secondary px-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
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
          <motion.div variants={item} className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-primary" />
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">National Overview</span>
          </motion.div>

          <motion.div variants={container} className="grid grid-cols-2 gap-2">
            <StatCard icon={<Users className="w-3.5 h-3.5" />} label="Visitors" value={fmt(summary.total_visitors)} />
            <StatCard icon={<Globe className="w-3.5 h-3.5" />} label="International" value={`${fmt(summary.international_visitors)}`} sub={`${(summary.international_visitors / summary.total_visitors * 100).toFixed(0)}%`} />
            <StatCard icon={<Hotel className="w-3.5 h-3.5" />} label="Hotels" value={summary.total_hotels.toString()} />
            <StatCard icon={<BarChart3 className="w-3.5 h-3.5" />} label="Rooms" value={fmt(summary.total_rooms)} />
          </motion.div>

          <motion.div variants={item}>
            <Card className="bg-card border-border/60">
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
          </motion.div>

          {summary.high_priority_zones > 0 && (
            <motion.div variants={item}>
              <Card className="bg-card border-destructive/40">
                <CardContent className="pt-4 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-destructive" />
                  <span className="text-xs">
                    <strong className="text-destructive">{summary.high_priority_zones}</strong> high-priority zones need investment
                  </span>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </>
      )}

      {/* Governorate Detail */}
      {govDetail && selectedGovId && (
        <motion.div variants={container} initial="hidden" animate="show">
          <motion.div variants={item}>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onGovSelect(null)}
              className="text-primary hover:text-primary/80 -ml-2 mb-2"
            >
              <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to National
            </Button>
          </motion.div>

          <motion.div variants={item}>
            <Card className="bg-card border-border/60">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{govDetail.governorate.name_en}</CardTitle>
                <div className="text-xs text-muted-foreground">{govDetail.governorate.name_ar}</div>
              </CardHeader>
              <CardContent className="space-y-3">
                <motion.div variants={container} className="grid grid-cols-2 gap-2">
                  <motion.div variants={item}><MiniStat label="Population" value={fmt(govDetail.governorate.population)} /></motion.div>
                  <motion.div variants={item}><MiniStat label="Area" value={`${fmt(govDetail.governorate.area_km2)} km²`} /></motion.div>
                  <motion.div variants={item}><MiniStat label="Hotels" value={govDetail.accommodation.hotel_count.toString()} /></motion.div>
                  <motion.div variants={item}><MiniStat label="Rooms" value={fmt(govDetail.accommodation.total_rooms)} /></motion.div>
                </motion.div>

                <Separator />

                {govDetail.visitors.length > 0 && (
                  <motion.div variants={item}>
                    <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">Visitor Trend</div>
                    <TimeSeriesChart
                      data={govDetail.visitors}
                      title=""
                      color="var(--primary)"
                      height={120}
                    />
                  </motion.div>
                )}

                {govDetail.occupancy.length > 0 && (
                  <motion.div variants={item}>
                    <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">Occupancy</div>
                    <TimeSeriesChart
                      data={govDetail.occupancy.map((o: any) => ({ year: o.year, month: o.month, total: o.rate }))}
                      title=""
                      color="#22c55e"
                      height={120}
                    />
                  </motion.div>
                )}

                {govDetail.indicators && (
                  <>
                    <Separator />
                    <motion.div variants={item}>
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
                    </motion.div>
                  </>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      )}
    </motion.div>
  );
}
