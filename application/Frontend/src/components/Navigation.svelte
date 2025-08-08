<script>
  import { push } from 'svelte-spa-router';
  import { isAuthenticated, setAuthenticated, user as authUserStore } from '../stores/authStore.js';

  let menuOpen = false;
  function goTo(path) {
    push(path);
    menuOpen = false; // Close menu on navigation
  }
  function logout() {
    localStorage.removeItem('access_token');
    setAuthenticated(false);
    push('/login');
    menuOpen = false;
  }
  function toggleMenu() {
    menuOpen = !menuOpen;
  }
</script>

<nav class="navbar">
  <div class="navbar-left">
    <a href="/" class="logo-icon" on:click|preventDefault={() => goTo('/')}>
      <img src="/icons/agora-icon.png" alt="Agora" />
    </a>
    <button class="hamburger" on:click={toggleMenu} aria-label="Toggle navigation">
      <span></span><span></span><span></span>
    </button>
  </div>

  <div class="navbar-center {menuOpen ? 'open' : ''}">
    <a href="/" class="nav-link" on:click|preventDefault={() => goTo('/')}>Home</a>
    <a href="/skill-sharing" class="nav-link" on:click|preventDefault={() => goTo('/skill-sharing')}>Skill Sharing</a>
    <a href="/about" class="nav-link" on:click|preventDefault={() => goTo('/about')}>About</a>
    <a href="/post" class="nav-link" on:click|preventDefault={() => goTo('/post')}>Post</a>
    <a href="/messages" class="nav-link" on:click|preventDefault={() => goTo('/messages')}>Messages</a>
    <a href="/post-skill" class="nav-link" on:click|preventDefault={() => goTo('/post-skill')}>Post Skill</a>
    {#if $isAuthenticated}
      <a href="/my-listings" class="nav-link" on:click|preventDefault={() => goTo('/my-listings')}>My Listings</a>
    {/if}
    {#if $isAuthenticated && $authUserStore && $authUserStore.is_admin}
      <a href="/admin/approve-listings" class="nav-link" on:click|preventDefault={() => goTo('/admin/approve-listings')}>Admin Panel</a>
    {/if}
  </div>

  <div class="navbar-right {menuOpen ? 'open' : ''}">
    {#if $isAuthenticated}
      <button class="nav-link" on:click={logout}>Logout</button>
    {/if}
    {#if !$isAuthenticated}
      <a href="/login" class="nav-link" on:click|preventDefault={() => goTo('/login')}>Login</a>
    {/if}
  </div>
</nav>

<style>
.navbar {
  position: sticky;
  top: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  background: white;
  margin-top: 1.5rem;
  padding: 0.6rem 1.5rem;
  box-shadow: 0 8px 20px rgba(106, 27, 154, 0.25), 0 4px 8px rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  border: 1px solid #e5d4f3;
  max-width: 95%;
  margin-left: auto;
  margin-right: auto;
  height: 50px;
}

.logo-icon {
  padding: 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon img {
  height: 50px;
  width: 50px;
  object-fit: contain;
  vertical-align: middle;
}

.navbar-left {
  flex: 0 0 auto;
  margin-left: 4rem;
  display: flex;
  align-items: center;
}

.hamburger {
  display: none;
  flex-direction: column;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: none;
  border: none;
  cursor: pointer;
  margin-left: 1rem;
}
.hamburger span {
  height: 4px;
  width: 100%;
  background: #4a148c;
  margin: 4px 0;
  border-radius: 2px;
  transition: 0.3s;
}

.navbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
  gap: 1.2rem;
  margin-left: auto;
  margin-right: auto;
  max-width: 700px;
}

.navbar-right {
  flex: 0 0 auto;
  display: flex;
  gap: 1rem;
}

.nav-link {
  color: #4a148c;
  text-decoration: none;
  font-size: 1rem;
  font-weight: 600;
  padding: 0.4rem 0.7rem;
  border-radius: 6px;
  white-space: nowrap;
  transition: background 0.2s, color 0.2s;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
}

.nav-link:hover,
button.nav-link:hover,
.logo-icon:hover {
  background: #9711ac;
  color: #ffffff;
}

@media (max-width: 768px) {
  .navbar {
    flex-direction: column;
    align-items: flex-start;
    padding: 1rem;
    height: auto;
  }
  .navbar-left {
    margin-left: 0;
    margin-bottom: 0.5rem;
  }
  .hamburger {
    display: flex;
  }
  .navbar-center,
  .navbar-right {
    display: none;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
    width: 100%;
    margin-top: 0.5rem;
    background: white;
    box-shadow: 0 2px 8px rgba(106, 27, 154, 0.08);
    position: absolute;
    left: 0;
    top: 60px;
    z-index: 1001;
    padding: 1rem;
  }
  .navbar-center.open,
  .navbar-right.open {
    display: flex;
  }
  .nav-link, button.nav-link {
    width: 100%;
    padding: 0.5rem 0;
    text-align: left;
  }
}
</style>