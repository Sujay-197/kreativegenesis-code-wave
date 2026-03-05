import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import Particles from '../components/Particles';
import { ArrowRight, ShoppingBag, Calendar, Users, BarChart3, ClipboardList, Truck } from 'lucide-react';

const examples = [
  {
    icon: ShoppingBag,
    title: 'Bakery Order Tracker',
    persona: 'Simple Mode',
    description: 'A small bakery owner tracks customer orders, manages status from received to delivered, and keeps a customer list.',
    entities: ['Orders', 'Customers', 'Products'],
    time: '8 minutes',
  },
  {
    icon: Calendar,
    title: 'Clinic Appointment System',
    persona: 'Simple Mode',
    description: 'A clinic receptionist books patient appointments, tracks doctor availability, and sends reminders.',
    entities: ['Appointments', 'Patients', 'Doctors'],
    time: '11 minutes',
  },
  {
    icon: Users,
    title: 'NGO Volunteer Manager',
    persona: 'Simple Mode',
    description: 'An NGO coordinator manages volunteer sign-ups, assigns tasks, and tracks hours contributed per project.',
    entities: ['Volunteers', 'Projects', 'Tasks'],
    time: '9 minutes',
  },
  {
    icon: BarChart3,
    title: 'Sales Pipeline Dashboard',
    persona: 'Expert Mode',
    description: 'A technical founder builds a CRM-lite with deal stages, contact management, and revenue forecasting.',
    entities: ['Deals', 'Contacts', 'Activities'],
    time: '6 minutes',
  },
  {
    icon: ClipboardList,
    title: 'Internal Tool: HR Onboarding',
    persona: 'Expert Mode',
    description: 'An engineering team builds an onboarding checklist tool with role-based access for HR and new hires.',
    entities: ['Employees', 'Tasks', 'Roles'],
    time: '7 minutes',
  },
  {
    icon: Truck,
    title: 'Delivery Route Planner',
    persona: 'Simple Mode',
    description: 'A logistics coordinator plans daily delivery routes, assigns drivers, and tracks delivery status.',
    entities: ['Deliveries', 'Drivers', 'Routes'],
    time: '10 minutes',
  },
];

export default function Examples() {
  return (
    <>
      <Header />
      <main className="relative">
        <div className="absolute inset-0 pointer-events-none">
          <div style={{ width: '100%', height: '100%', position: 'absolute' }}>
            <Particles
              particleColors={["#ffffff"]}
              particleCount={200}
              particleSpread={10}
              speed={0.1}
              particleBaseSize={100}
              moveParticlesOnHover={false}
              alphaParticles={false}
              disableRotation={false}
              pixelRatio={1}
            />
          </div>
        </div>
        <section className="pt-32 pb-16 bg-forge-dark relative z-10">
          <div className="max-w-4xl mx-auto px-6 lg:px-8 text-center">
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="font-heading text-5xl md:text-6xl font-bold text-white mb-6"
            >
              What people are building
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-forge-muted text-xl leading-relaxed"
            >
              Real apps built through conversation. From bakeries to engineering teams.
            </motion.p>
          </div>
        </section>

        <section className="py-16 bg-forge-darker border-t border-forge-border">
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {examples.map((ex, i) => (
                <motion.div
                  key={ex.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.07 }}
                  className="group p-8 rounded-2xl border border-forge-border bg-forge-surface hover:border-forge-accent/30 hover:-translate-y-1 hover:shadow-lg transition-all duration-300"
                >
                  <div className="flex items-start justify-between mb-5">
                    <div className="w-12 h-12 rounded-xl bg-forge-accent/10 flex items-center justify-center group-hover:bg-forge-accent/20 transition-colors duration-300">
                      <ex.icon size={22} className="text-forge-accent" />
                    </div>
                    <span
                      className={`text-xs font-semibold px-3 py-1 rounded-full ${
                        ex.persona === 'Simple Mode'
                          ? 'bg-forge-accent/15 text-forge-accent'
                          : 'bg-forge-emerald/15 text-forge-emerald'
                      }`}
                    >
                      {ex.persona}
                    </span>
                  </div>

                  <h2 className="font-heading font-bold text-white text-xl mb-3">{ex.title}</h2>
                  <p className="text-forge-muted text-sm leading-relaxed mb-5">{ex.description}</p>

                  <div className="flex flex-wrap gap-2 mb-5">
                    {ex.entities.map((e) => (
                      <span
                        key={e}
                        className="text-xs px-2.5 py-1 rounded-lg bg-forge-border/50 text-forge-muted-light border border-forge-border"
                      >
                        {e}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-xs text-forge-muted">Built in {ex.time}</span>
                    <Link
                      to="/builder"
                      className="text-xs text-forge-accent hover:text-forge-accent-hover font-semibold flex items-center gap-1 transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent rounded"
                    >
                      Build similar
                      <ArrowRight size={12} />
                    </Link>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-16 bg-forge-dark border-t border-forge-border">
          <div className="max-w-4xl mx-auto px-6 lg:px-8 text-center">
            <h2 className="font-heading text-3xl font-bold text-white mb-4">
              Your idea is next
            </h2>
            <p className="text-forge-muted mb-8">
              If you can describe it, InNovus can build it.
            </p>
            <Link
              to="/builder"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-forge-accent hover:bg-forge-accent-hover text-white font-semibold transition-all duration-200 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-accent focus-visible:ring-offset-2 focus-visible:ring-offset-forge-dark"
            >
              Start Building Free
              <ArrowRight size={18} />
            </Link>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}