import { THEME } from "@/lib/constants";

interface TooltipProps {
  text: string;
  children: React.ReactNode;
}

export default function Tooltip({ text, children }: TooltipProps) {
  return (
    <span style={{ position: "relative", display: "inline-block", cursor: "help" }}>
      {children}
      <span
        style={{
          visibility: "hidden",
          opacity: 0,
          position: "absolute",
          bottom: "120%",
          left: "50%",
          transform: "translateX(-50%)",
          backgroundColor: THEME.surfaceAlt,
          color: THEME.text,
          padding: "6px 10px",
          borderRadius: 6,
          border: `1px solid ${THEME.border}`,
          fontSize: 11,
          whiteSpace: "nowrap",
          zIndex: 100,
          transition: "opacity 0.2s",
          pointerEvents: "none",
          maxWidth: 250,
          whiteSpace: "normal" as any,
        }}
        className="tooltip-content"
      >
        {text}
      </span>
      <style jsx>{`
        span:hover .tooltip-content {
          visibility: visible;
          opacity: 1;
        }
      `}</style>
    </span>
  );
}

// Indicator explanations (English + Arabic)
export const INDICATOR_EXPLANATIONS: Record<string, { en: string; ar: string }> = {
  "rooms_per_1000": {
    en: "Number of hotel rooms available per 1,000 visitors. Higher = more capacity per visitor (less stress). Lower = fewer rooms per visitor (more stress).",
    ar: "عدد غرف الفنادق المتاحة لكل 1000 زائر. أعلى = مساحة أكبر لكل زائر. أقل = ضغط أكبر على السعة.",
  },
  "beds_per_1000": {
    en: "Number of beds available per 1,000 visitors. Similar to rooms but accounts for multi-bed rooms.",
    ar: "عدد الأسرة المتاحة لكل 1000 زائر.",
  },
  "occupancy_pressure": {
    en: "Combined measure of average and peak hotel occupancy rates. Higher = more pressure on capacity. Scale: 0-100.",
    ar: "مقياس مدمج لمعدلات الإشغال المتوسطة والقصوى للفنادق. أعلى = ضغط أكبر على السعة.",
  },
  "growth_pressure": {
    en: "Year-over-year visitor growth rate. Positive = growing demand (more pressure). Negative = declining demand.",
    ar: "معدل نمو الزوار السنوي. موجب = طلب متزايد. سالب = طلب منخفض.",
  },
  "capacity_adequacy": {
    en: "Ratio of accommodation supply to visitor demand. >1 = surplus (over-capacity). <1 = deficit (under-capacity). =1 = balanced.",
    ar: "نسبة المعروض من الإقامة إلى الطلب على الزوار. >1 = فائض. <1 = عجز. =1 = متوازن.",
  },
  "priority_score": {
    en: "Investment priority score (0-100). Higher = more urgent need for tourism infrastructure investment.",
    ar: "درجة أولوية الاستثمار (0-100). أعلى = حاجة أكثر إلحاحاً للاستثمار في البنية التحتية للسياحة.",
  },
  "classification": {
    en: "Capacity status: UNDER (needs investment), BALANCED (adequate), OVER (excess supply).",
    ar: "حالة السعة: تحت (يحتاج استثمار), متوازن (كافٍ), فوق (فائض في المعروض).",
  },
  "demand_score": {
    en: "Score based on forecasted visitor demand. Higher demand = higher score = more investment needed.",
    ar: "درجة بناءً على الطلب المتوقع على الزوار. طلب أعلى = درجة أعلى = مزيد من الاستثمار.",
  },
  "capacity_gap_score": {
    en: "Score based on the gap between accommodation supply and demand. Positive gap = under-capacity = needs investment.",
    ar: "درجة بناءً على الفجوة بين المعروض من الإقامة والطلب. فجوة إيجابية = نقص في السعة.",
  },
};
