<script>
  import { push } from 'svelte-spa-router';

  export let title       = "Discover and Share Skills!";
  export let description = "Learn, teach, and grow together in our community.";
  export let buttonText  = "Explore Skill Sharing";
  export let link        = "/skill-sharing";
  export let imageUrl    = "/styles/purple-background.jpg";

  function go() {
    push(link);
  }
</script>

<div
  class="promo-card"
  style="background-image: url('{imageUrl}');"
>
  <div class="promo-content">
    <h2>{title}</h2>
    <p>{description}</p>
    <button class="promo-button" on:click={go}>
      {buttonText}
    </button>
  </div>
</div>

<style>
  .promo-card {
    position: sticky;
    top: 100px;
    width: 100%;
    max-width: 280px;
    margin: 40px auto;
    border-radius: 12px;
    overflow: hidden;
    background-size: cover;
    background-position: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    display: flex;
    align-items: flex-end;
    justify-content: center;
  }

  .promo-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }

  .promo-content {
    position: relative;
    z-index: 1;
    padding: 24px;
    width: 100%;
    background: linear-gradient(
      to top,
      rgba(0, 0, 0, 0.3),
      rgba(0, 0, 0, 0)
    );
    text-align: center;
  }

  .promo-content h2 {
    margin: 0;
    font-size: 1.8rem;
    line-height: 1.2;
    color: #fff;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
  }

  .promo-content p {
    margin: 8px 0 16px;
    font-size: 1rem;
    color: #fafafa;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  }

  .promo-button {
    padding: 12px 24px;
    background-color: rgba(255, 255, 255, 0.85);
    color: #6a1b9a;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.3s ease, transform 0.2s ease;
  }

  .promo-button:hover {
    background-color: #fff;
    transform: translateY(-2px);
  }
</style>


