import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import App from './App.jsx';
import './style.css';

// Report expired sessions from any API request.
// 한글: 모든 API 요청에서 세션 만료를 공통으로 알린다.
const originalFetch = window.fetch.bind(window);
window.fetch = async (...args) => {
  const response = await originalFetch(...args);
  const url = typeof args[0] === 'string' ? args[0] : args[0].url;
  if (response.status === 401 && url.includes('/api/') && !url.includes('/api/session')) window.dispatchEvent(new Event('session-expired'));
  return response;
};

function SecureApp() {
  const [role, setRole] = useState(null);
  const [checking, setChecking] = useState(true);
  const [username, setUsername] = useState('operator');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changeError, setChangeError] = useState('');
  const [changeBusy, setChangeBusy] = useState(false);
  useEffect(() => {
    fetch('/api/session', {cache: 'no-store'}).then(r => r.ok ? r.json() : null)
      .then(data => setRole(data?.role || null)).catch(() => setError('서버에 연결할 수 없습니다.'))
      .finally(() => setChecking(false));
  }, []);
  useEffect(() => {
    const expired = () => { setRole(null); setPassword(''); setError('세션이 만료되었습니다. 다시 로그인해 주세요.'); };
    window.addEventListener('session-expired', expired);
    return () => window.removeEventListener('session-expired', expired);
  }, []);
  async function signIn(event) {
    event.preventDefault(); setError('');
    try {
      const response = await fetch('/api/session/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({username, password})});
      if (response.status === 429) { setError('로그인 시도가 너무 많습니다. 잠시 후 다시 시도하세요.'); return; }
      if (response.status === 401) { setError('계정과 비밀번호를 확인하세요.'); return; }
      if (!response.ok) { setError('로그인 서버에 문제가 발생했습니다. 잠시 후 다시 시도하세요.'); return; }
      setRole((await response.json()).role); setPassword('');
    } catch { setError('서버에 연결할 수 없습니다. 네트워크 연결을 확인하세요.'); }
  }
  if (checking) return <main className="login-panel">연결을 확인하고 있습니다.</main>;
  if (!role) return <main className="login-panel"><form onSubmit={signIn}><h1>JetInspect 로그인</h1><p>안전한 HTTPS 연결을 확인하세요.</p><label>계정<input autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} /></label><label>비밀번호<input type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} /></label>{error && <p role="alert">{error}</p>}<button type="submit">로그인</button></form></main>;
  async function signOut() { try { await fetch('/api/session/logout', {method:'POST'}); } catch { /* Clear local session state even if offline. */ } finally { setRole(null); setPassword(''); } }
  function closePassword() { setChangingPassword(false); setCurrentPassword(''); setNewPassword(''); setConfirmPassword(''); setChangeError(''); }
  async function submitPassword(event) {
    event.preventDefault(); setChangeError('');
    if (newPassword.length < 12 || newPassword.length > 256) { setChangeError('새 비밀번호는 12자 이상 256자 이하여야 합니다.'); return; }
    if (newPassword !== confirmPassword) { setChangeError('새 비밀번호 확인이 일치하지 않습니다.'); return; }
    setChangeBusy(true);
    try {
      const response = await fetch('/api/session/password', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({current_password: currentPassword, new_password: newPassword})});
      const data = await response.json();
      if (response.status === 401) { closePassword(); setRole(null); setError('세션이 만료되었습니다. 다시 로그인해 주세요.'); return; }
      if (!response.ok) {
        const messages = {invalid_current_password: '현재 비밀번호가 올바르지 않습니다.', invalid_password: '새 비밀번호는 12자 이상 256자 이하여야 합니다.', password_unchanged: '현재와 다른 비밀번호를 입력하세요.', try_later: '시도가 너무 많습니다. 잠시 후 다시 시도하세요.'};
        setChangeError(messages[data.error] || '비밀번호를 변경하지 못했습니다. 잠시 후 다시 시도하세요.'); return;
      }
      closePassword(); setRole(null); setPassword(''); setError('비밀번호가 변경되었습니다. 새 비밀번호로 다시 로그인해 주세요.');
    } catch { setChangeError('서버에 연결할 수 없습니다. 연결 상태를 확인하세요.'); }
    finally { setChangeBusy(false); }
  }
  return <><App role={role} onSignOut={signOut} onChangePassword={() => setChangingPassword(true)}/>{changingPassword && <div className="password-overlay"><section className="password-dialog" role="dialog" aria-modal="true" aria-labelledby="password-title"><h2 id="password-title">비밀번호 변경</h2><p>변경 후 이 계정의 모든 기기에서 다시 로그인해야 합니다.</p><form onSubmit={submitPassword}><label>현재 비밀번호<input type="password" autoComplete="current-password" value={currentPassword} onChange={event => setCurrentPassword(event.target.value)} required autoFocus/></label><label>새 비밀번호<input type="password" autoComplete="new-password" minLength="12" maxLength="256" value={newPassword} onChange={event => setNewPassword(event.target.value)} required/></label><label>새 비밀번호 확인<input type="password" autoComplete="new-password" minLength="12" maxLength="256" value={confirmPassword} onChange={event => setConfirmPassword(event.target.value)} required/></label>{changeError && <p role="alert">{changeError}</p>}<div className="password-actions"><button type="button" disabled={changeBusy} onClick={closePassword}>취소</button><button type="submit" disabled={changeBusy}>{changeBusy ? '변경 중…' : '변경하기'}</button></div></form></section></div>}</>;
}

createRoot(document.getElementById('root')).render(<SecureApp/>);
