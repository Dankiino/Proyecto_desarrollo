const Button = ({ label, onClick, variant = "primary", disabled = false, type = "button" }) => {
  return (
    <button
      type={type}
      className={`btn btn-${variant}`}
      onClick={onClick}
      disabled={disabled}
    >
      {label}
    </button>
  );
};

export default Button;