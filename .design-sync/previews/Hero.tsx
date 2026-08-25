import { Button, Hero } from '@aditf/design-system';

export function Default() {
  return (
    <div style={{ background: 'var(--ink)' }}>
      <Hero
        trackingLabel="TRACKING NO."
        trackingValue="AF-2011–2026"
        status="IN TRANSIT"
        name="Aditya"
        nameAccent="Firmansyah"
        role="Senior Software Engineer — Full-Stack Developer"
        origin="SURAKARTA, ID"
        dest="WORLDWIDE"
        lede="Thirteen-plus years shipping web, backend, and mobile software — from enterprise logistics platforms moving real packages to the microservices that route them."
        actions={
          <>
            <Button variant="stamp" href="assets/Aditya_Firmansyah_CV.pdf" download>
              Download CV
            </Button>
            <Button variant="ghost" href="#contact">
              Get in touch
            </Button>
          </>
        }
      />
    </div>
  );
}
