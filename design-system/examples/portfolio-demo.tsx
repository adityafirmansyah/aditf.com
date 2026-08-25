import {
  Barcode,
  Button,
  ContactGrid,
  CrateGrid,
  Hero,
  LabelCard,
  LangChip,
  Nav,
  ProjectCard,
  Reveal,
  RouteProgress,
  Seal,
  SectionHead,
  StatRow,
  Timeline,
} from '../src';

const navLinks = [
  { label: 'About', href: '#about', index: '01' },
  { label: 'Skills', href: '#skills', index: '02' },
  { label: 'Projects', href: '#projects', index: '03' },
  { label: 'Experience', href: '#experience', index: '04' },
  { label: 'Certs', href: '#certifications', index: '05' },
  { label: 'Contact', href: '#contact', index: '06' },
];

export default function PortfolioDemo() {
  return (
    <>
      <RouteProgress />
      <Nav mark="AF" links={navLinks} />

      <main id="top">
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

        <section className="section" id="about">
          <SectionHead eyebrow="Manifest — Contents Declaration" title="About" />
          <Reveal>
            <LabelCard>
              Software engineer with 13+ years designing and building scalable web, backend, and
              mobile applications, from enterprise logistics platforms to AI-integrated SaaS.
            </LabelCard>
          </Reveal>
          <Reveal>
            <StatRow
              stats={[
                { num: '13+', label: 'Years Shipping Code' },
                { num: '6', label: 'Portals & Apps Built at pickupp' },
                { num: '2', label: 'Languages — ID Native / EN Professional' },
              ]}
            />
          </Reveal>
        </section>

        <section className="section" id="skills">
          <SectionHead eyebrow="Cargo Manifest — Technical Payload" title="Skills" />
          <Reveal>
            <CrateGrid
              groups={[
                { label: 'Frontend', items: ['React', 'Next.js', 'React Native'] },
                { label: 'Backend', items: ['Node.js', 'NestJS', 'REST APIs', 'gRPC'] },
              ]}
            />
          </Reveal>
        </section>

        <section className="section" id="projects">
          <SectionHead eyebrow="Cargo Log — Personal Freight" title="Projects" />
          <div className="project-list">
            <Reveal>
              <ProjectCard
                eyebrow="Solo Build — Full-Stack Rust"
                title="GainForge"
                subtitle="Gamified Fitness RPG"
                badge={{ label: 'LIVE', href: 'https://gainforgeapp.com' }}
                lede="GainForge turns real workouts into RPG quests — users earn XP, level up a character, and grow four stats by completing daily training sessions."
                points={[
                  'Full Rust stack front-to-back — Leptos (WASM) frontend and an Axum backend share a single DTO crate.',
                  'Designed the quest/XP/leveling system and a 4-stat character model.',
                ]}
                stack={['Rust', 'Leptos (WASM)', 'Axum', 'PostgreSQL', 'Docker']}
                cta={{ label: 'Visit GainForge', href: 'https://gainforgeapp.com' }}
              />
            </Reveal>
          </div>
        </section>

        <section className="section" id="experience">
          <SectionHead eyebrow="Shipment History — Tracking Log" title="Experience" />
          <Reveal>
            <Timeline
              items={[
                {
                  date: 'Aug 2024 – Jul 2026',
                  status: 'In Transit',
                  statusVariant: 'transit',
                  role: 'CTO',
                  org: 'GOSG Consulting',
                  bullets: ['Leads product and architecture for a platform spanning website creation, e-commerce, and SEO tooling.'],
                  stack: ['Website Builder', 'E-commerce', 'AI Agents'],
                },
                {
                  date: 'Apr 2019 – Jul 2024',
                  status: 'Delivered',
                  role: 'Software Engineer',
                  org: 'pickupp, Singapore',
                  bullets: ['Developed and maintained enterprise logistics platforms using React, Next.js, Node.js, and NestJS.'],
                  stack: ['React', 'Next.js', 'Kubernetes', 'gRPC'],
                },
              ]}
            />
          </Reveal>
        </section>

        <section className="section" id="certifications">
          <SectionHead eyebrow="Quality Control — Certified Seals" title="Certifications & Languages" />
          <Reveal>
            <div className="seal-row">
              <Seal label="JavaScript" sublabel="Course" />
              <Seal label="CSS" sublabel="Fundamentals" />
            </div>
          </Reveal>
          <Reveal>
            <div className="lang-row">
              <LangChip name="Indonesian" level="Native" />
              <LangChip name="English" level="Professional Working Proficiency" />
            </div>
          </Reveal>
        </section>

        <section className="section section--contact" id="contact">
          <Barcode />
          <SectionHead eyebrow="Consignee Details — Final Destination" title="Let's ship something together." />
          <Reveal>
            <ContactGrid
              rows={[
                { label: 'Email', value: 'aditf.work@gmail.com', href: 'mailto:aditf.work@gmail.com' },
                { label: 'Location', value: 'Surakarta, Central Java, Indonesia' },
                { label: 'GitHub', value: '/adityafirmansyah', href: 'https://github.com/adityafirmansyah' },
              ]}
            />
          </Reveal>
        </section>
      </main>
    </>
  );
}
