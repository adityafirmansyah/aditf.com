export interface WaybillProps {
  label: string;
  value: string;
  status?: string;
}

export function Waybill({ label, value, status }: WaybillProps) {
  return (
    <div className="waybill">
      <span className="waybill__field">
        {label} <b>{value}</b>
      </span>
      {status ? (
        <>
          <span className="waybill__divider" aria-hidden="true">·</span>
          <span className="waybill__status">
            <i className="dot" aria-hidden="true" />
            {status}
          </span>
        </>
      ) : null}
    </div>
  );
}
