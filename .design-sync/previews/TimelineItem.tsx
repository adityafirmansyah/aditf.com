import { TimelineItem } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, maxWidth: 720 };

export function WithoutStack() {
  return (
    <div style={wrapperStyle}>
      <ol className="timeline">
        <TimelineItem
          date="May 2018 – Apr 2019"
          status="Delivered"
          role="Full-Stack Developer"
          org="WebDesignHamburg.net"
          bullets={[
            'Developed and maintained custom web applications for international clients.',
            'Implemented frontend and backend features based on business requirements.',
            'Delivered responsive and maintainable web solutions.',
          ]}
        />
      </ol>
    </div>
  );
}
