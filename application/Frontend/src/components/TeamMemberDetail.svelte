<script>
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';

  // Props passed by the router
  export let params = {};

  let memberId = '';
  let memberDetails = null; // Placeholder for actual member data

  // Placeholder data - In a real app, you'd fetch this based on memberId
  const allTeamMembers = {
    'nathan': {
      name: 'Nathan Delos Reyes',
      role: 'Team Lead',
      image: '/Images/nathan.png',
      bio: "My name is Nathan Delos Reyes. I’m a senior at SFSU. I’m the team lead for this project. I oversee the project and communicate directly with the CTO. I’m looking forward to learning more about the leadership position and the other aspects my team is working on. When I’m not working, I like to watch movies and play Kendama."
    },
    'ranbir': {
      name: 'Ranbir Atkar',
      role: 'Front-end Lead',
      image: '/Images/Ranbir.png',
      bio: "My name is Ranbir Atkar, and I am a senior Computer Science student at San Francisco State University. In this project, I am serving as the lead frontend developer. My partner, Jose, and I will work together to ensure that the frontend is intuitive, user-friendly, and seamless. As the lead frontend developer, I am deeply passionate about software development. I am eager to expand my expertise and deepen my understanding of backend development and overall software architecture. In my free time, I enjoy exploring new activities and seeking out adventures. I also prioritize fitness and enjoy working out when time allows."
    },
    'jose': {
      name: 'Jose Ramirez',
      role: 'Front-end Lead Helper',
      image: '/Images/jose.webp',
      bio: "Hi, my name is Jose Ramirez, and I'm a Computer Science student at San Francisco State University. In this project, I'm helping with frontend development, working on creating a smooth and user-friendly interface. While my focus is on frontend, I'm also eager to learn more about Git/Github and backend development to gain a deeper understanding of the full software development process. I have also been able to work on an e-commerce site in my CSC 317 course, where I gained experience with html, css, git, and javascript. Outside of coding, I'm a big collector of Funko Pops and sneakers."
    },
    'jeshwanth': {
      name: 'Jeshwanth Ravindra Singh',
      role: 'Back-end Lead',
      image: '/Images/jeshwanth.png',
      bio: "I'm Jeshwanth, a San Francisco State University Computer Science student graduating in Spring 2025. I'm passionate about software development, with a strong focus on front-end design, back-end systems, and AI-powered applications. I'm currently working on backend development for a team project, focusing on building efficient APIs, database management, and server-side logic, sharpening my Git/GitHub workflows, and improving front-end integration to ensure a seamless user experience."
    },
    'xiaoxuan': {
      name: 'Xiaoxuan Wang',
      role: 'GitHub Master',
      image: '/Images/xia.jpg',
      bio: "Hi, my name is Xiaoxuan Wang, and I'm a Computer Science student at San Francisco State University. In this project, my main role is a GitHub master. I gained most of my experience with Git/Github from team projects in school and some open-source projects. I am responsible for managing the project repository and ensuring that all team members are following the agreed practices. I look forward to gaining more experience in both frontend and backend development in this project. In my free time, I like olympic weightlifting and playing rugby."
    }
  };

  onMount(() => {
    memberId = params.memberId || 'unknown';
    memberDetails = allTeamMembers[memberId];
    console.log("Displaying details for member ID:", memberId);
  });

  function goBack() {
    push('/about'); // Go back to the About page
  }
</script>

<div class="container">
  <button on:click={goBack} class="back-link">← Back to About</button>

  {#if memberDetails}
    <div class="member-detail-card">
      <img src={memberDetails.image} alt={memberDetails.name} class="member-image"/>
      <h1>{memberDetails.name}</h1>
      <h2>{memberDetails.role}</h2>
      <p>{memberDetails.bio || 'No bio available.'}</p>
      <!-- Add more details as needed -->
    </div>
  {:else}
    <p>Team member details not found for ID: {memberId}</p>
  {/if}
</div>

<style>
  .container {
    max-width: 700px;
    margin: 40px auto;
    padding: 20px;
  }

  .back-link {
    color: #6a1b9a;
    text-decoration: none;
    font-weight: bold;
    font-size: 1rem;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    margin-bottom: 20px;
    display: inline-block;
  }
  .back-link:hover {
    text-decoration: underline;
  }

  .member-detail-card {
    background-color: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    text-align: center;
  }

  .member-image {
    width: 150px;
    height: 150px;
    border-radius: 50%;
    object-fit: cover;
    margin-bottom: 20px;
    border: 4px solid #f0e6f6; /* Light purple border */
  }

  h1 {
    color: #333;
    font-size: 2em;
    margin-bottom: 5px;
  }

  h2 {
    color: #6a1b9a; /* Theme color */
    font-size: 1.2em;
    font-weight: 500;
    margin-bottom: 20px;
  }

  p {
    color: #555;
    font-size: 1rem;
    line-height: 1.6;
  }
</style>