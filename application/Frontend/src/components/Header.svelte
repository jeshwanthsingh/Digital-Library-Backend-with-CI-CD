<script>
  import { push } from 'svelte-spa-router';

  function goTo(path) {
    push(path);
  }
</script>

<div class="header">
  <p class="disclaimer">
    SFSU Software Engineering Project CSC 648-848, Spring 2025. For Demonstration Only
  </p>
  <div class="header-content">
    <a href="/" class="header-link" on:click|preventDefault={() => goTo('/')}>
      <h1>Agora - SFSU Community Marketplace</h1>
    </a>
  </div>
</div>

<style>
  .header {
    position: relative;
    width: 100%;
    height: 200px;
    background-image: url('/styles/purple-agora.png');
    background-size: cover;
    background-position: bottom right;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: white;
  }

  .disclaimer {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    color: white;
    text-align: center;
    font-size: 0.85rem;
    padding-top: 0.5rem;
  }

  .header-content {
    z-index: 1;
  }

  .header-link {
    text-decoration: none;
    color: inherit;
    display: inline-block;
    cursor: pointer;
  }

  .header h1 {
    font-size: 2.5rem;
    color: white;
    text-shadow: 0 0 8px rgba(255, 255, 255, 0.4),
                 0 0 20px rgba(255, 255, 255, 0.2);
    margin: 0;
  }

  @media (max-width: 600px) {
    .header h1 {
      font-size: 1.5rem;
    }
  }
</style>

  