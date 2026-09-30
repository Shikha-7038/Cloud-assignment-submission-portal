import React from "react";

const LABELS = {
  NOT_SUBMITTED: "Not submitted",
  SUBMITTED: "Submitted",
  LATE: "Late",
  GRADED: "Graded",
};

export default function StatusBadge({ status }) {
  return <span className={`badge status-${status}`}>{LABELS[status] || status}</span>;
}
