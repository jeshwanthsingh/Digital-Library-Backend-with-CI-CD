<script>
  import { link } from 'svelte-spa-router'; // Import the link action

  // Team members data with unique IDs
  const teamMembers = [
    {
      id: 'nathan',
      name: 'Nathan Delos Reyes',
      role: 'Team Lead',
      // Add image path if available
      image: '/Images/nathan.png' // Assuming image is in public/Images
    },
    {
      id: 'ranbir',
      name: 'Ranbir Atkar',
      role: 'Front-end Lead',
      image: '/Images/Ranbir.png'
    },
    {
      id: 'jose',
      name: 'Jose Ramirez',
      role: 'Front-end Lead Helper',
      image: '/Images/jose.webp'
    },
    {
      id: 'jeshwanth',
      name: 'Jeshwanth Ravindra Singh',
      role: 'Back-end Lead',
      image: '/Images/jeshwanth.png'
    },
    {
      id: 'xiaoxuan',
      name: 'Xiaoxuan Wang',
      role: 'GitHub Master',
      image: '/Images/xia.jpg'
    }
  ];
</script>

<div class="container">
  <h1>About Our Team</h1>

  <p>
    Our mission is to create a digital marketplace for SFSU students, teachers, and faculty to buy and sell books, music, notes, and other educational materials. We aim to provide an easy and secure platform for the community to trade these items.
  </p>

  <div class="team-members">
    {#each teamMembers as member (member.id)}
      <a href={`/team/${member.id}`} use:link class="team-member-card">
        <img src={member.image} alt={member.name} class="team-member-image"/>
        <div class="team-member-info">
          <span class="team-member-name">{member.name}</span>
          <span class="team-member-role">{member.role}</span>
        </div>
      </a>
    {/each}
  </div>
</div>

<style>
  .container {
    max-width: 800px;
    margin: 40px auto;
    padding: 30px;
    text-align: center;
    background-color: white;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }

  h1 {
    color: #333;
    margin-bottom: 30px;
    font-size: 2.5em;
    position: relative;
    padding-bottom: 15px;
  }

  h1:after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 100px;
    height: 3px;
    background: #6a1b9a; /* Changed to match theme color */
  }

  p {
    color: #444;
    font-size: 1.1em;
    max-width: 700px;
    margin: 30px auto;
    text-align: left;
    padding: 25px;
    background-color: #f8f9fa;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }

  .team-members {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); /* Responsive grid */
    gap: 25px;
    margin-top: 40px;
    text-align: left;
  }

  .team-member-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    text-decoration: none;
    color: inherit;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }

  .team-member-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
  }

  .team-member-image {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    object-fit: cover;
    margin-bottom: 15px;
    border: 3px solid #fff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  .team-member-info {
    text-align: center;
  }

  .team-member-name {
    display: block;
    font-weight: 600;
    color: #6a1b9a; /* Theme color */
    font-size: 1.1rem;
    margin-bottom: 5px;
  }

  .team-member-role {
    display: block;
    font-size: 0.9rem;
    color: #555;
  }
</style>
