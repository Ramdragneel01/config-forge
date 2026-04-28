type StatusBadgeProps = {
    status: "draft" | "validated" | "rejected" | "promoted";
};

export function StatusBadge({ status }: StatusBadgeProps) {
    const className = `status-badge status-${status}`;
    return <span className={className}>{status}</span>;
}
