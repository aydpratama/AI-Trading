'use client';

import React, { useState, useEffect } from 'react';
import { Menu, Bell, Grid, User, Moon, Sun, Wallet, Loader2, Building2, LogIn, Settings, Brain, BarChart2 } from 'lucide-react';
import { getAccount, getBrokers, loginBroker, type Account, type BrokersResponse } from '@/lib/api';

export default function Header({
  toggleSidebar,
  theme,
  toggleTheme,
  onTradeClick,
  onSettingsClick,
  onAnalyticsClick,
  aiConnected,
  aiProvider
}: {
  toggleSidebar: () => void,
  theme: string,
  toggleTheme: () => void,
  onTradeClick?: () => void,
  onSettingsClick?: () => void,
  onAnalyticsClick?: () => void,
  aiConnected?: boolean,
  aiProvider?: string
}) {
  const [account, setAccount] = useState<Account | null>(null);
  const [brokers, setBrokers] = useState<BrokersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [showBrokerMenu, setShowBrokerMenu] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginForm, setLoginForm] = useState({ login: '', password: '', server: '' });
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState('');

  const loadData = async () => {
    try {
      const [accountData, brokersData] = await Promise.all([
        getAccount(),
        getBrokers()
      ]);
      setAccount(accountData);
      setBrokers(brokersData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-10 border-b bg-background/95 backdrop-blur-md flex items-center justify-between px-3 sm:px-4">
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="p-1 -ml-1 rounded-md hover:bg-accent text-muted-foreground dark:text-white hover:text-foreground md:hidden transition-colors"
        >
          <Menu size={18} />
        </button>

        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-900/20">
            <Grid className="text-white" size={12} />
          </div>
          <span className="font-bold text-sm tracking-tight text-foreground dark:text-white">
            Trading<span className="text-blue-500">AYDP</span>
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onTradeClick}
          className="hidden sm:flex items-center gap-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-full text-xs font-bold transition-all shadow-lg shadow-blue-900/20 mr-2 active:scale-95"
        >
          TRADE
        </button>

        {/* Broker Status - Clickable to show menu */}
        <div className="relative hidden sm:block">
          <button
            onClick={() => setShowBrokerMenu(!showBrokerMenu)}
            className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium transition-all ${brokers?.current?.connected
              ? 'bg-green-600/10 border border-green-600/20 text-green-600 dark:text-green-400'
              : 'bg-red-600/10 border border-red-600/20 text-red-600 dark:text-red-400'
              }`}
          >
            <div className={`w-2 h-2 rounded-full ${brokers?.current?.connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <Building2 size={14} />
            <span>{brokers?.current?.server || 'Not Connected'}</span>
          </button>

          {/* Broker Dropdown Menu */}
          {showBrokerMenu && (
            <div className="absolute top-full right-0 mt-1 w-48 bg-card border border-border rounded-lg shadow-lg z-50 py-1">
              <div className="px-3 py-1.5 text-[10px] text-muted-foreground uppercase tracking-wide border-b">
                Akun Broker
              </div>
              {brokers?.current?.connected && (
                <div className="px-3 py-2 text-xs">
                  <div className="font-medium text-green-600">{brokers.current.server}</div>
                  <div className="text-muted-foreground text-[10px]">Terhubung</div>
                </div>
              )}
              <div className="border-t mt-1 pt-1">
                <button
                  onClick={() => {
                    setShowBrokerMenu(false);
                    setShowLoginModal(true);
                    setLoginForm({ login: '', password: '', server: '' });
                    setLoginError('');
                  }}
                  className="w-full text-left px-3 py-2 text-xs text-blue-500 hover:bg-accent transition-colors flex items-center gap-2"
                >
                  <LogIn size={14} />
                  Login Broker Baru
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Login Broker Modal */}
        {showLoginModal && (
          <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={() => setShowLoginModal(false)}>
            <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-sm p-5 my-auto" onClick={e => e.stopPropagation()}>
              <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
                <Building2 size={16} />
                Login Broker MT5
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Akun (Login)</label>
                  <input
                    type="text"
                    value={loginForm.login}
                    onChange={e => setLoginForm({ ...loginForm, login: e.target.value })}
                    placeholder="Contoh: 12345678"
                    className="w-full h-8 px-3 text-xs bg-secondary border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Sandi</label>
                  <input
                    type="password"
                    value={loginForm.password}
                    onChange={e => setLoginForm({ ...loginForm, password: e.target.value })}
                    placeholder="Masukkan sandi"
                    className="w-full h-8 px-3 text-xs bg-secondary border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Server</label>
                  <input
                    type="text"
                    value={loginForm.server}
                    onChange={e => setLoginForm({ ...loginForm, server: e.target.value })}
                    placeholder="Contoh: Exness-Real"
                    className="w-full h-8 px-3 text-xs bg-secondary border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                {loginError && (
                  <div className="text-xs text-red-500 bg-red-500/10 p-2 rounded-md">
                    {loginError}
                  </div>
                )}
              </div>
              <div className="flex gap-2 mt-4">
                <button
                  onClick={() => setShowLoginModal(false)}
                  className="flex-1 h-8 text-xs border border-border rounded-md hover:bg-accent transition-colors"
                  disabled={loginLoading}
                >
                  Batal
                </button>
                <button
                  onClick={async () => {
                    if (!loginForm.login || !loginForm.password || !loginForm.server) {
                      setLoginError('Semua field harus diisi');
                      return;
                    }
                    setLoginLoading(true);
                    setLoginError('');
                    try {
                      const result = await loginBroker({
                        login: parseInt(loginForm.login),
                        password: loginForm.password,
                        server: loginForm.server
                      });
                      if (result.success) {
                        setShowLoginModal(false);
                        loadData(); // Refresh data
                      } else {
                        setLoginError(result.message);
                      }
                    } catch (error) {
                      setLoginError('Gagal terhubung ke server');
                    } finally {
                      setLoginLoading(false);
                    }
                  }}
                  disabled={loginLoading}
                  className="flex-1 h-8 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loginLoading ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      Menghubungkan...
                    </>
                  ) : (
                    'Login'
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-blue-600/10 border border-blue-600/20 text-xs font-medium text-blue-600 dark:text-blue-400 cursor-pointer hover:bg-blue-600/20 transition-all">
          {loading ? (
            <Loader2 size={14} className="animate-spin" />
          ) : account ? (
            <>
              <Wallet size={14} />
              <span>${account.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            </>
          ) : (
            <>
              <Wallet size={14} />
              <span>$12,450.00</span>
            </>
          )}
        </div>

        {/* AI Status + Settings */}
        <button
          onClick={onSettingsClick}
          className={`flex items-center gap-1.5 p-1.5 rounded-full hover:bg-accent transition-colors ${aiConnected ? 'text-purple-600 dark:text-purple-400' : 'text-muted-foreground dark:text-white hover:text-foreground'
            }`}
          title="Pengaturan"
        >
          {aiConnected && <span className="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse" />}
          <Settings size={16} />
        </button>

        <button
          onClick={onAnalyticsClick}
          className="p-1.5 rounded-full hover:bg-accent text-muted-foreground dark:text-white hover:text-foreground transition-colors"
          title="Analytics"
        >
          <BarChart2 size={16} />
        </button>

        <button
          onClick={toggleTheme}
          className="p-1.5 rounded-full hover:bg-accent text-muted-foreground dark:text-white hover:text-foreground transition-colors"
          title={theme === 'dark' ? "Mode Terang" : "Mode Gelap"}
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        <button className="p-1.5 rounded-full hover:bg-accent text-muted-foreground dark:text-white hover:text-foreground transition-colors relative">
          <Bell size={16} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-blue-500 rounded-full"></span>
        </button>

        <button className="w-7 h-7 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-border flex items-center justify-center hover:ring-1 hover:ring-blue-500 transition-all">
          <User size={14} className="text-muted-foreground dark:text-white" />
        </button>
      </div>
    </header>
  );
}
