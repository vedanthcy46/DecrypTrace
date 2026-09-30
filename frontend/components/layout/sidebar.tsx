'use client';
import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, LayoutDashboard, Send, Inbox, Search, Database } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

export function Sidebar() {
  const pathname = usePathname();
  
  const navItems = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard, color: '#3B82F6' },
    { name: 'Sender', href: '/sender', icon: Send, color: '#8B5CF6' },
    { name: 'Recipient', href: '/recipient', icon: Inbox, color: '#10B981' },
    { name: 'Investigator', href: '/investigator', icon: Search, color: '#F59E0B' },
    { name: 'Ledger', href: '/ledger', icon: Database, color: '#3B82F6' },
  ];

  return (
    <div className="w-64 h-screen bg-[#111827] border-r border-[#1E293B] flex flex-col">
      <div className="p-6 flex items-center space-x-3">
        <Shield className="w-8 h-8 text-[#3B82F6]" />
        <span className="text-xl font-bold text-white tracking-wide">DecrypTrace</span>
      </div>
      
      <nav className="flex-1 px-4 space-y-2 mt-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link key={item.name} href={item.href}>
              <div className={cn(
                'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors cursor-pointer relative overflow-hidden',
                isActive ? 'bg-[#1E293B] text-white' : 'text-[#94A3B8] hover:bg-[#1E293B]/50 hover:text-[#E2E8F0]'
              )}>
                {isActive && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute left-0 w-1 h-full rounded-r-md"
                    style={{ backgroundColor: item.color }}
                  />
                )}
                <Icon className={cn('w-5 h-5', isActive && `text-[${item.color}]`)} />
                <span className="font-medium">{item.name}</span>
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-[#1E293B]">
        <div className="text-xs font-semibold text-[#94A3B8] uppercase tracking-wider mb-3">System Status</div>
        <div className="space-y-2">
          {[1, 2, 3].map((node) => (
            <div key={node} className="flex items-center justify-between">
              <span className="text-sm text-[#E2E8F0]">DLT Node {node}</span>
              <div className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
