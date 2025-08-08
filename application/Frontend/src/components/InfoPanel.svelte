<script>
    export let title = "Why Join Agora?";
    export let items = [
      "Exclusive SFSU community marketplace",
      "Buy and sell textbooks, electronics, and more",
      "Find tutors and skill-sharing services",
      "Safe on-campus exchanges",
      "Connect with fellow SFSU students"
    ];
  </script>
  
  <div class="login-info">
    <h3>{title}</h3>
    <ul>
      {#each items as item}
        <li>
          <i class="info-icon">✓</i>
          <span>{item}</span>
        </li>
      {/each}
    </ul>
  </div>
  <style>
    .login-info {
    background-color: var(--card-background);
    border-radius: 12px;
    box-shadow: var(--shadow-md);
    padding: 40px;
    width: 380px;
    position: relative;
    overflow: hidden;
}

.login-info::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 6px;
    background: linear-gradient(90deg, var(--secondary-color), var(--primary-color));
}

.login-info h3 {
    color: var(--primary-color);
    margin-bottom: 24px;
    font-size: 24px;
    position: relative;
    display: inline-block;
}

.login-info h3::after {
    content: '';
    position: absolute;
    bottom: -5px;
    left: 0;
    width: 30px;
    height: 3px;
    background-color: var(--secondary-color);
}

.login-info ul {
    list-style-type: none;
}

.login-info li {
    display: flex;
    align-items: flex-start;
    margin-bottom: 18px;
    position: relative;
    padding-left: 30px;
}

.info-icon {
    position: absolute;
    left: 0;
    top: 2px;
    color: var(--secondary-color);
    font-size: 18px;
    background-color: rgba(255, 193, 7, 0.1);
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
}

.login-info li span {
    font-size: 15px;
    line-height: 1.6;
}

/* Animation for InfoPanel */
.login-info {
    animation: fadeUp 0.8s ease-out;
}

/* Related media queries for responsiveness */
@media screen and (max-width: 1100px) {
    .login-info {
        width: 350px;
    }
}

@media screen and (max-width: 900px) {
    .login-info {
        width: 100%;
        max-width: 550px;
        margin: 0 auto;
        margin-top: 30px;
    }
}

@media screen and (max-width: 600px) {
    .login-info {
        padding: 30px 20px;
    }
}

/* Required variable definitions if not already included elsewhere */
:root {
    --primary-color: #5E35B1;
    --secondary-color: #FFC107;
    --card-background: #FFFFFF;
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Required animation keyframe if not already included elsewhere */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
  </style>