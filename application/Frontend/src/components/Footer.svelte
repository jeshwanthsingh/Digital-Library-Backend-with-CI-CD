<script>
    import { push } from 'svelte-spa-router';

function goTo(path) {
  push(path);
}
</script>

<footer>
  <div class="footer-content">
    <p>&copy; 2025 Agora SFSU Marketplace</p>
    <div class="footer-links">
        <a href="/about" class="nav-link" on:click|preventDefault={() => goTo('/about')}>About</a>
      <a href="/terms">Terms of Service</a>
      <a href="/privacy">Privacy Policy</a>
      <a href="/contact">Contact</a>
    </div>
  </div>
</footer>

<style>
footer {
    background: linear-gradient(135deg, #212121, #424242);
    color: white;
    padding: 30px 5%;
    margin-top: 60px;
}

.footer-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
}

.footer-links a {
    color: #e0e0e0;
    margin-left: 24px;
    font-size: 14px;
    transition: var(--transition);
    position: relative;
}

.footer-links a::after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 0;
    width: 0;
    height: 2px;
    background-color: var(--secondary-color);
    transition: var(--transition);
}

.footer-links a:hover {
    color: white;
    text-decoration: none;
}

.footer-links a:hover::after {
    width: 100%;
}
@media screen and (max-width: 600px) {
    .footer-content {
        flex-direction: column;
        gap: 20px;
    }
    
    .footer-links {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 15px;
    }
    
    .footer-links a {
        margin: 0;
    }
}
</style>