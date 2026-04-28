type MetricTileProps = {
  title: string;
  value: string;
  subtitle: string;
};

export function MetricTile({ title, value, subtitle }: MetricTileProps) {
  return (
    <article className="metric-tile">
      <h3>{title}</h3>
      <p className="metric-value">{value}</p>
      <p className="metric-subtitle">{subtitle}</p>
    </article>
  );
}
