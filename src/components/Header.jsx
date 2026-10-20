const Header = ({ title, description }) => {
  return (
    <header className="header-container text-center">
      <h1 className="header-title">{title}</h1>
      <p className="header-subtitle">{description}</p>
    </header>
  );
};

export default Header;