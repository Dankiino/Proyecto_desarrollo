const Card = ({ titulo, children }) => {
  return (
    <div className="card">
      {titulo && <h2 className="section-title text-center">{titulo}</h2>}
      {children}
    </div>
  );
};

export default Card;